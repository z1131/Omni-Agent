"""
文本感知处理器
"""

import uuid
from typing import AsyncIterator
from datetime import datetime

from ..events import PerceptionEvent, ModalityType, EventStage


class TextPerceptionHandler:
    """文本感知处理器（最简单）"""
    
    async def process(self, text: str) -> AsyncIterator[PerceptionEvent]:
        """处理文本输入
        
        Args:
            text: 文本内容
            
        Yields:
            感知事件
        """
        yield PerceptionEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            modality=ModalityType.TEXT,
            stage=EventStage.FINAL,
            content=text,
            confidence=1.0,
            timestamp=datetime.now(),
        )
