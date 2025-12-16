"""
Omni-Agent 感知层

将外部信号转译为结构化认知事件
"""

from .base import (
    PerceptionEvent,
    ModalityType,
    EventStage,
    PerceptionPipeline,
)

from .stt import (
    SttService,
    SttConfig,
    SttResult,
    WordInfo,
    AliyunSttService,
    MockSttService,
    SttRegistry,
)

__all__ = [
    # Base
    'PerceptionEvent',
    'ModalityType',
    'EventStage',
    'PerceptionPipeline',
    # STT
    'SttService',
    'SttConfig',
    'SttResult',
    'WordInfo',
    'AliyunSttService',
    'MockSttService',
    'SttRegistry',
]
