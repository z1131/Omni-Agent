"""
模态处理器

根据输入类型选择对应的感知服务
"""

from .router import ModalityRouter
from .audio_handler import AudioPerceptionHandler
from .text_handler import TextPerceptionHandler

__all__ = [
    'ModalityRouter',
    'AudioPerceptionHandler',
    'TextPerceptionHandler',
]
