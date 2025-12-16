"""
STT (Speech-to-Text) 服务

提供语音转文字能力
"""

from .base import SttService, SttConfig, SttResult, WordInfo
from .aliyun import AliyunSttService, MockSttService, SttRegistry

__all__ = [
    'SttService',
    'SttConfig', 
    'SttResult',
    'WordInfo',
    'AliyunSttService',
    'MockSttService',
    'SttRegistry',
]
