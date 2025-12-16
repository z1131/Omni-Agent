"""
感知事件定义

所有模态的输入最终都被转换为统一的感知事件
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class ModalityType(Enum):
    """模态类型"""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"


class EventStage(Enum):
    """事件阶段"""
    PARTIAL = "partial"     # 中间结果（如 STT 实时识别）
    FINAL = "final"         # 最终结果
    ERROR = "error"         # 错误


@dataclass
class PerceptionEvent:
    """感知事件 - 所有模态输入的统一表示"""
    
    event_id: str
    modality: ModalityType
    stage: EventStage
    content: str                    # 文本化内容
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 原始数据（可选）
    raw_data: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "modality": self.modality.value,
            "stage": self.stage.value,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
