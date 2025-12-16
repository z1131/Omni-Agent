"""
模态路由

根据输入类型选择对应的处理器
"""

from typing import Dict, Optional
from ..events import ModalityType


class ModalityRouter:
    """模态路由 - 根据输入类型选择感知服务"""
    
    def __init__(self):
        self._handlers: Dict[ModalityType, 'PerceptionHandler'] = {}
        self._init_handlers()
    
    def _init_handlers(self):
        """初始化处理器"""
        from .audio_handler import AudioPerceptionHandler
        from .text_handler import TextPerceptionHandler
        
        self._handlers = {
            ModalityType.AUDIO: AudioPerceptionHandler(),
            ModalityType.TEXT: TextPerceptionHandler(),
        }
    
    def get_handler(self, modality: ModalityType) -> Optional['PerceptionHandler']:
        """获取对应模态的处理器"""
        return self._handlers.get(modality)
    
    def register_handler(self, modality: ModalityType, handler: 'PerceptionHandler'):
        """注册自定义处理器"""
        self._handlers[modality] = handler
