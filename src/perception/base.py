"""
感知层基础抽象

按照 docs/01_FEATURES/感知层设计.md 实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import time


class ModalityType(Enum):
    """模态类型"""
    TEXT = "text"
    AUDIO = "audio"
    VISION = "vision"
    DATA = "data"


class EventStage(Enum):
    """事件阶段"""
    PARTIAL = "partial"    # 增量/中间结果
    FINAL = "final"        # 最终结果


@dataclass
class PerceptionEvent:
    """感知层统一输出事件
    
    所有感知管道的输出都统一为此格式
    """
    # 事件标识
    event_id: str
    session_id: str
    
    # 模态信息
    modality: ModalityType
    source: str                    # e.g., "stt_aliyun", "ocr_paddle"
    
    # 事件状态
    stage: EventStage
    timestamp_ms: int
    
    # 内容
    content: str                   # 主要内容（文本）
    confidence: float = 1.0        # 置信度 [0, 1]
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 原始数据引用（可选）
    raw_data_ref: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'session_id': self.session_id,
            'modality': self.modality.value,
            'source': self.source,
            'stage': self.stage.value,
            'timestamp_ms': self.timestamp_ms,
            'content': self.content,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'raw_data_ref': self.raw_data_ref,
        }
    
    @classmethod
    def create(
        cls,
        session_id: str,
        modality: ModalityType,
        source: str,
        stage: EventStage,
        content: str,
        **kwargs
    ) -> 'PerceptionEvent':
        """便捷创建方法"""
        return cls(
            event_id=f"pe_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            modality=modality,
            source=source,
            stage=stage,
            timestamp_ms=int(time.time() * 1000),
            content=content,
            **kwargs
        )


# 事件回调类型
EventCallback = Callable[[PerceptionEvent], Awaitable[None]]


class PerceptionPipeline(ABC):
    """感知管道基类
    
    所有感知管道（Audio、Vision、Data）都需要继承此类
    """
    
    def __init__(self):
        self._callbacks: List[EventCallback] = []
        self._session_id: Optional[str] = None
        self._running: bool = False
    
    @property
    @abstractmethod
    def modality(self) -> ModalityType:
        """返回管道处理的模态类型"""
        ...
    
    @abstractmethod
    async def start(self, session_id: str, config: Dict[str, Any]) -> None:
        """启动管道
        
        Args:
            session_id: 会话 ID
            config: 管道配置
        """
        ...
    
    @abstractmethod
    async def stop(self) -> None:
        """停止管道"""
        ...
    
    @abstractmethod
    async def feed(self, data: bytes) -> None:
        """输入原始数据
        
        Args:
            data: 原始数据（音频、图像等）
        """
        ...
    
    def on_event(self, callback: EventCallback) -> None:
        """注册事件回调
        
        Args:
            callback: 异步回调函数，接收 PerceptionEvent
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: EventCallback) -> None:
        """移除事件回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _emit(self, event: PerceptionEvent) -> None:
        """发射事件到所有回调"""
        for callback in self._callbacks:
            try:
                await callback(event)
            except Exception as e:
                # 回调异常不应影响管道运行
                from ..infra import get_logger
                logger = get_logger(__name__)
                logger.error(f"Event callback error", exc=e)
    
    @property
    def is_running(self) -> bool:
        """管道是否运行中"""
        return self._running
    
    @property
    def session_id(self) -> Optional[str]:
        """当前会话 ID"""
        return self._session_id
