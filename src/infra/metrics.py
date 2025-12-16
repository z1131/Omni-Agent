"""
Omni-Agent 埋点服务

按照 docs/04_OPS/埋点规范.md 实现
支持：
- 标准事件模型
- 自动埋点装饰器
- 阿里云 SLS 集成
- 批量异步发送
"""

import os
import time
import json
import uuid
import asyncio
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from contextlib import contextmanager
from functools import wraps
from contextvars import ContextVar

from .logging import _trace_context, get_logger

logger = get_logger(__name__)


class EventStatus(Enum):
    """事件状态"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class MetricEvent:
    """埋点事件"""
    event_id: str
    event_type: str
    event_name: str
    timestamp: str
    status: str = "success"
    
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    duration_ms: Optional[int] = None
    
    dimensions: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'event_name': self.event_name,
            'timestamp': self.timestamp,
            'status': self.status,
        }
        
        if self.trace_id:
            result['trace_id'] = self.trace_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.user_id:
            result['user_id'] = self.user_id
        if self.duration_ms is not None:
            result['duration_ms'] = self.duration_ms
        if self.dimensions:
            result['dimensions'] = self.dimensions
        if self.metrics:
            result['metrics'] = self.metrics
        if self.error:
            result['error'] = self.error
        if self.extra:
            result['extra'] = self.extra
        
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class MetricsService:
    """埋点服务"""
    
    def __init__(
        self,
        enabled: bool = True,
        sls_config: Optional[Dict[str, Any]] = None,
        batch_size: int = 200,
        flush_interval: float = 5.0,
        sampling_rate: float = 1.0
    ):
        self.enabled = enabled
        self.sls_config = sls_config
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.sampling_rate = sampling_rate
        
        self._buffer: List[Dict] = []
        self._lock = threading.Lock()
        self._client = None
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        
        # 采样规则
        self._sampling_rules: Dict[str, float] = {}
        
        if self.enabled:
            self._init_client()
            self._start_flush_thread()
    
    def _init_client(self):
        """初始化 SLS 客户端"""
        if not self.sls_config or not self.sls_config.get('enabled'):
            return
        
        try:
            from aliyun.log import LogClient
            self._client = LogClient(
                self.sls_config['endpoint'],
                self.sls_config['access_key_id'],
                self.sls_config['access_key_secret']
            )
        except ImportError:
            logger.warn("aliyun-log-python-sdk not installed, SLS disabled")
            self._client = None
    
    def _start_flush_thread(self):
        """启动定时刷新线程"""
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
    
    def _flush_loop(self):
        """定时刷新循环"""
        while self._running:
            time.sleep(self.flush_interval)
            self._flush()
    
    def _should_sample(self, event_type: str) -> bool:
        """判断是否采样"""
        rate = self._sampling_rules.get(event_type, self.sampling_rate)
        if rate >= 1.0:
            return True
        import random
        return random.random() < rate
    
    def set_sampling_rule(self, event_type: str, rate: float):
        """设置采样规则"""
        self._sampling_rules[event_type] = rate
    
    def track(
        self,
        event_type: str,
        event_name: str,
        status: EventStatus = EventStatus.SUCCESS,
        duration_ms: Optional[int] = None,
        dimensions: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, float]] = None,
        error: Optional[Dict[str, Any]] = None,
        **extra
    ) -> None:
        """记录埋点事件
        
        Args:
            event_type: 事件类型，如 "llm.call", "tool.call"
            event_name: 事件名称，如 "llm_call_complete"
            status: 事件状态
            duration_ms: 耗时（毫秒）
            dimensions: 维度字段（用于分组聚合）
            metrics: 指标字段（数值型）
            error: 错误信息
            **extra: 扩展字段
        """
        if not self.enabled:
            return
        
        # 采样判断
        if not self._should_sample(event_type):
            return
        
        # 获取上下文
        ctx = _trace_context.get()
        
        # 构建事件
        event = MetricEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            event_name=event_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=status.value if isinstance(status, EventStatus) else status,
            trace_id=ctx.get('trace_id'),
            session_id=ctx.get('session_id'),
            user_id=ctx.get('user_id'),
            duration_ms=duration_ms,
            dimensions=dimensions or {},
            metrics=metrics or {},
            error=error,
            extra=extra
        )
        
        # 添加到缓冲区
        with self._lock:
            self._buffer.append(event.to_dict())
            
            if len(self._buffer) >= self.batch_size:
                self._flush()
    
    @contextmanager
    def track_duration(
        self,
        event_type: str,
        event_name: str,
        dimensions: Optional[Dict[str, str]] = None,
        **extra
    ):
        """自动记录操作耗时的上下文管理器
        
        Usage:
            with metrics.track_duration("tool.call", "tool_call_complete", 
                                        dimensions={"tool_name": "web_search"}):
                result = await tool.execute(params)
        """
        start_time = time.time()
        status = EventStatus.SUCCESS
        error_info = None
        
        try:
            yield
        except Exception as e:
            status = EventStatus.ERROR
            error_info = {
                'code': type(e).__name__,
                'message': str(e)
            }
            raise
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            self.track(
                event_type=event_type,
                event_name=event_name,
                status=status,
                duration_ms=duration_ms,
                dimensions=dimensions,
                error=error_info,
                **extra
            )
    
    def _flush(self):
        """刷新缓冲区"""
        with self._lock:
            if not self._buffer:
                return
            
            events_to_send = self._buffer.copy()
            self._buffer.clear()
        
        # 发送到 SLS
        if self._client and self.sls_config:
            self._send_to_sls(events_to_send)
        else:
            # 本地输出（开发环境）
            for event in events_to_send:
                logger.debug(f"Metric: {event['event_type']}.{event['event_name']}", **event)
    
    def _send_to_sls(self, events: List[Dict]):
        """发送到 SLS"""
        try:
            from aliyun.log import PutLogsRequest, LogItem
            
            log_items = []
            for event in events:
                contents = [(k, json.dumps(v) if isinstance(v, (dict, list)) else str(v))
                           for k, v in self._flatten_dict(event).items()]
                log_items.append(LogItem(contents=contents))
            
            request = PutLogsRequest(
                project=self.sls_config['project'],
                logstore=self.sls_config.get('metrics_logstore', 'metrics-logs'),
                topic='',
                source='',
                logitems=log_items
            )
            self._client.put_logs(request)
        except Exception as e:
            logger.error("Failed to send metrics to SLS", exc=e)
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict) and v:
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def close(self):
        """关闭服务"""
        self._running = False
        self._flush()


def tracked(
    event_type: str,
    dimensions_from_args: Optional[List[str]] = None,
    metrics_from_result: Optional[List[str]] = None
):
    """自动埋点装饰器
    
    Args:
        event_type: 事件类型
        dimensions_from_args: 从函数参数提取的维度字段名
        metrics_from_result: 从返回值提取的指标字段名
    
    Usage:
        @tracked(
            event_type="llm.call",
            dimensions_from_args=["model"],
            metrics_from_result=["tokens"]
        )
        async def call_llm(model: str, messages: List[Dict]) -> LLMResponse:
            ...
    """
    def decorator(func):
        func_name = func.__name__
        start_event = f"{func_name}_start"
        complete_event = f"{func_name}_complete"
        error_event = f"{func_name}_error"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics()
            
            # 提取维度
            dimensions = {}
            if dimensions_from_args:
                for arg_name in dimensions_from_args:
                    if arg_name in kwargs:
                        dimensions[arg_name] = str(kwargs[arg_name])
            
            # 开始事件
            metrics.track(event_type, start_event, dimensions=dimensions)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                # 提取指标
                result_metrics = {}
                if metrics_from_result and result is not None:
                    for metric_name in metrics_from_result:
                        if hasattr(result, metric_name):
                            result_metrics[metric_name] = getattr(result, metric_name)
                        elif isinstance(result, dict) and metric_name in result:
                            result_metrics[metric_name] = result[metric_name]
                
                # 完成事件
                metrics.track(
                    event_type, complete_event,
                    status=EventStatus.SUCCESS,
                    duration_ms=duration_ms,
                    dimensions=dimensions,
                    metrics=result_metrics
                )
                return result
            
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                metrics.track(
                    event_type, error_event,
                    status=EventStatus.ERROR,
                    duration_ms=duration_ms,
                    dimensions=dimensions,
                    error={'code': type(e).__name__, 'message': str(e)}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics()
            
            dimensions = {}
            if dimensions_from_args:
                for arg_name in dimensions_from_args:
                    if arg_name in kwargs:
                        dimensions[arg_name] = str(kwargs[arg_name])
            
            metrics.track(event_type, start_event, dimensions=dimensions)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_metrics = {}
                if metrics_from_result and result is not None:
                    for metric_name in metrics_from_result:
                        if hasattr(result, metric_name):
                            result_metrics[metric_name] = getattr(result, metric_name)
                        elif isinstance(result, dict) and metric_name in result:
                            result_metrics[metric_name] = result[metric_name]
                
                metrics.track(
                    event_type, complete_event,
                    status=EventStatus.SUCCESS,
                    duration_ms=duration_ms,
                    dimensions=dimensions,
                    metrics=result_metrics
                )
                return result
            
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                metrics.track(
                    event_type, error_event,
                    status=EventStatus.ERROR,
                    duration_ms=duration_ms,
                    dimensions=dimensions,
                    error={'code': type(e).__name__, 'message': str(e)}
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# 全局单例
_metrics: Optional[MetricsService] = None


def get_metrics() -> MetricsService:
    """获取全局埋点服务"""
    global _metrics
    if _metrics is None:
        _metrics = MetricsService(
            enabled=os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
            sampling_rate=float(os.getenv('METRICS_SAMPLING_RATE', '1.0'))
        )
    return _metrics


def setup_metrics(
    enabled: bool = True,
    sls_config: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """初始化埋点服务
    
    Args:
        enabled: 是否启用
        sls_config: SLS 配置
        **kwargs: 其他配置（batch_size, flush_interval, sampling_rate）
    """
    global _metrics
    _metrics = MetricsService(
        enabled=enabled,
        sls_config=sls_config,
        **kwargs
    )
    return _metrics
