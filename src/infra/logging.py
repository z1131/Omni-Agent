"""
Omni-Agent 统一日志服务

按照 docs/04_OPS/日志规范.md 实现
支持：
- 结构化 JSON 日志
- 链路追踪 (trace_id)
- 阿里云 SLS 集成
- 多输出目标（控制台、文件、SLS）
"""

import os
import sys
import json
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from functools import wraps
import threading

# 上下文变量，用于存储当前请求的追踪信息
_trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})


def generate_trace_id() -> str:
    """生成链路追踪 ID
    
    格式：{timestamp_hex}_{random_hex}_{instance_id}
    """
    timestamp_hex = format(int(time.time()), 'x')[:8]
    random_hex = uuid.uuid4().hex[:8]
    instance_id = os.getenv('INSTANCE_ID', 'local')[:16]
    return f"{timestamp_hex}_{random_hex}_{instance_id}"


@dataclass
class LogRecord:
    """结构化日志记录"""
    timestamp: str
    level: str
    logger: str
    message: str
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'timestamp': self.timestamp,
            'level': self.level,
            'logger': self.logger,
            'message': self.message,
        }
        if self.trace_id:
            result['trace_id'] = self.trace_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.context:
            result['context'] = self.context
        if self.extra:
            result['extra'] = self.extra
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 获取上下文
        ctx = _trace_context.get()
        
        # 构建日志记录
        log_record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            trace_id=ctx.get('trace_id'),
            session_id=ctx.get('session_id'),
            context=getattr(record, 'context', {}),
            extra=ctx.get('extra', {})
        )
        
        # 添加异常信息
        if record.exc_info:
            log_record.context['exception'] = self.formatException(record.exc_info)
        
        return log_record.to_json()


class TextFormatter(logging.Formatter):
    """文本格式化器（开发环境友好）"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        ctx = _trace_context.get()
        trace_id = ctx.get('trace_id', '-')[:16]
        
        # 颜色
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # 时间
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        # 基础格式
        msg = f"{timestamp} {color}{record.levelname:7}{reset} [{trace_id}] {record.name} - {record.getMessage()}"
        
        # 添加 context
        context = getattr(record, 'context', {})
        if context:
            ctx_str = ' '.join(f"{k}={v}" for k, v in context.items())
            msg += f" | {ctx_str}"
        
        # 异常
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        
        return msg


class SLSHandler(logging.Handler):
    """阿里云 SLS 日志处理器
    
    批量异步发送日志到 SLS
    """
    
    def __init__(
        self,
        endpoint: str,
        project: str,
        logstore: str,
        access_key_id: str,
        access_key_secret: str,
        batch_size: int = 100,
        flush_interval: float = 3.0
    ):
        super().__init__()
        self.endpoint = endpoint
        self.project = project
        self.logstore = logstore
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._buffer: List[Dict] = []
        self._lock = threading.Lock()
        self._client = None
        self._flush_thread = None
        self._running = False
        
        self._init_client()
        self._start_flush_thread()
    
    def _init_client(self):
        """初始化 SLS 客户端"""
        try:
            from aliyun.log import LogClient
            self._client = LogClient(
                self.endpoint,
                self.access_key_id,
                self.access_key_secret
            )
        except ImportError:
            # SLS SDK 未安装，降级为本地日志
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
    
    def emit(self, record: logging.LogRecord):
        """处理日志记录"""
        try:
            # 解析 JSON 格式的消息
            msg = self.format(record)
            log_item = json.loads(msg)
            
            with self._lock:
                self._buffer.append(log_item)
                
                if len(self._buffer) >= self.batch_size:
                    self._flush()
        except Exception:
            self.handleError(record)
    
    def _flush(self):
        """刷新缓冲区到 SLS"""
        with self._lock:
            if not self._buffer:
                return
            
            logs_to_send = self._buffer.copy()
            self._buffer.clear()
        
        if self._client is None:
            return
        
        try:
            from aliyun.log import PutLogsRequest, LogItem
            
            log_items = []
            for log in logs_to_send:
                contents = [(k, str(v) if not isinstance(v, str) else v) 
                           for k, v in self._flatten_dict(log).items()]
                log_items.append(LogItem(contents=contents))
            
            request = PutLogsRequest(
                project=self.project,
                logstore=self.logstore,
                topic='',
                source='',
                logitems=log_items
            )
            self._client.put_logs(request)
        except Exception as e:
            # 发送失败，记录到本地
            sys.stderr.write(f"SLS send error: {e}\n")
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def close(self):
        """关闭处理器"""
        self._running = False
        self._flush()
        super().close()


class Logger:
    """Omni-Agent 日志接口"""
    
    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, exc: Optional[Exception] = None, **context):
        """通用日志方法"""
        extra = {'context': context}
        self._logger.log(level, message, exc_info=exc, extra=extra)
    
    def debug(self, message: str, **context) -> None:
        """调试日志"""
        self._log(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context) -> None:
        """信息日志"""
        self._log(logging.INFO, message, **context)
    
    def warn(self, message: str, **context) -> None:
        """警告日志"""
        self._log(logging.WARNING, message, **context)
    
    def error(self, message: str, exc: Optional[Exception] = None, **context) -> None:
        """错误日志"""
        self._log(logging.ERROR, message, exc=exc, **context)
    
    @contextmanager
    def span(self, operation: str):
        """自动记录操作耗时的上下文管理器"""
        span = LogSpan(self, operation)
        span.start()
        try:
            yield span
        except Exception as e:
            span.set_status('error')
            span.set_context('error', str(e))
            raise
        finally:
            span.end()


class LogSpan:
    """操作跨度，自动计算耗时"""
    
    def __init__(self, logger: Logger, operation: str):
        self._logger = logger
        self._operation = operation
        self._context: Dict[str, Any] = {}
        self._status = 'success'
        self._start_time: Optional[float] = None
    
    def start(self):
        """开始计时"""
        self._start_time = time.time()
        self._logger.debug(f"{self._operation} started")
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self._context[key] = value
    
    def set_status(self, status: str) -> None:
        """设置状态"""
        self._status = status
    
    def end(self):
        """结束计时并记录"""
        if self._start_time is None:
            return
        
        duration_ms = int((time.time() - self._start_time) * 1000)
        self._context['duration_ms'] = duration_ms
        self._context['status'] = self._status
        
        level = logging.INFO if self._status == 'success' else logging.ERROR
        self._logger._log(level, f"{self._operation} completed", **self._context)


@contextmanager
def log_context(
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **extra
):
    """设置当前上下文的日志追踪信息"""
    old_ctx = _trace_context.get()
    new_ctx = old_ctx.copy()
    
    if trace_id:
        new_ctx['trace_id'] = trace_id
    if session_id:
        new_ctx['session_id'] = session_id
    if extra:
        new_ctx.setdefault('extra', {}).update(extra)
    
    token = _trace_context.set(new_ctx)
    try:
        yield
    finally:
        _trace_context.reset(token)


def logged(level: str = "INFO", include_args: List[str] = None, include_result: bool = False):
    """自动记录函数调用的装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            # 提取参数
            context = {}
            if include_args:
                for arg_name in include_args:
                    if arg_name in kwargs:
                        context[arg_name] = kwargs[arg_name]
            
            logger.info(f"{func.__name__} started", **context)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_ctx = {'duration_ms': duration_ms}
                if include_result and result is not None:
                    result_ctx['result'] = str(result)[:200]
                
                logger.info(f"{func.__name__} completed", **result_ctx)
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(f"{func.__name__} failed", exc=e, duration_ms=duration_ms)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            context = {}
            if include_args:
                for arg_name in include_args:
                    if arg_name in kwargs:
                        context[arg_name] = kwargs[arg_name]
            
            logger.info(f"{func.__name__} started", **context)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                result_ctx = {'duration_ms': duration_ms}
                if include_result and result is not None:
                    result_ctx['result'] = str(result)[:200]
                
                logger.info(f"{func.__name__} completed", **result_ctx)
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.error(f"{func.__name__} failed", exc=e, duration_ms=duration_ms)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# 全局 Logger 缓存
_loggers: Dict[str, Logger] = {}


def get_logger(name: str) -> Logger:
    """获取 Logger 实例"""
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    sls_config: Optional[Dict[str, Any]] = None
):
    """初始化日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        format: 日志格式 (json, text)
        sls_config: SLS 配置，包含 endpoint, project, logstore, access_key_id, access_key_secret
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有 handler
    root_logger.handlers.clear()
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    if format == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(TextFormatter())
    root_logger.addHandler(console_handler)
    
    # SLS 输出
    if sls_config and sls_config.get('enabled'):
        sls_handler = SLSHandler(
            endpoint=sls_config['endpoint'],
            project=sls_config['project'],
            logstore=sls_config['logstore'],
            access_key_id=sls_config['access_key_id'],
            access_key_secret=sls_config['access_key_secret'],
            batch_size=sls_config.get('batch_size', 100),
            flush_interval=sls_config.get('flush_interval_ms', 3000) / 1000
        )
        sls_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(sls_handler)


# 默认初始化
def _default_init():
    """默认初始化（开发环境）"""
    level = os.getenv('LOG_LEVEL', 'INFO')
    format = os.getenv('LOG_FORMAT', 'text')
    setup_logging(level=level, format=format)


_default_init()
