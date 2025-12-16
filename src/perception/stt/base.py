"""
STT 服务抽象基类

按照 docs/01_FEATURES/感知层设计.md 实现
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class SttConfig:
    """STT 配置"""
    model: str = "default"
    language: str = "zh-CN"
    sample_rate: int = 16000
    enable_punctuation: bool = True
    enable_itn: bool = True              # Inverse Text Normalization
    hotwords: Optional[List[str]] = None  # 热词
    
    # 高级配置
    max_sentence_silence: int = 800      # 句子间静音时长(ms)
    enable_words: bool = False           # 是否返回词级时间戳
    
    def to_dict(self) -> dict:
        result = {
            'model': self.model,
            'language': self.language,
            'sample_rate': self.sample_rate,
            'enable_punctuation': self.enable_punctuation,
            'enable_itn': self.enable_itn,
            'max_sentence_silence': self.max_sentence_silence,
            'enable_words': self.enable_words,
        }
        if self.hotwords:
            result['hotwords'] = self.hotwords
        return result


@dataclass
class WordInfo:
    """词级信息"""
    word: str
    start_time_ms: int
    end_time_ms: int
    confidence: float = 1.0


@dataclass 
class SttResult:
    """STT 结果"""
    text: str
    is_final: bool
    confidence: float = 1.0
    start_time_ms: int = 0
    end_time_ms: int = 0
    words: Optional[List[WordInfo]] = None
    
    def to_dict(self) -> dict:
        result = {
            'text': self.text,
            'is_final': self.is_final,
            'confidence': self.confidence,
            'start_time_ms': self.start_time_ms,
            'end_time_ms': self.end_time_ms,
        }
        if self.words:
            result['words'] = [
                {
                    'word': w.word,
                    'start_time_ms': w.start_time_ms,
                    'end_time_ms': w.end_time_ms,
                    'confidence': w.confidence,
                }
                for w in self.words
            ]
        return result


# 回调类型
PartialCallback = Callable[[SttResult], None]
FinalCallback = Callable[[SttResult], None]
ErrorCallback = Callable[[Exception], None]
ReadyCallback = Callable[[], None]


class SttService(ABC):
    """STT 服务抽象基类
    
    所有 STT Provider 实现都需要继承此类
    """
    
    def __init__(self):
        self._on_partial: Optional[PartialCallback] = None
        self._on_final: Optional[FinalCallback] = None
        self._on_error: Optional[ErrorCallback] = None
        self._on_ready: Optional[ReadyCallback] = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 名称"""
        ...
    
    @abstractmethod
    async def start_session(
        self, 
        session_id: str, 
        config: SttConfig
    ) -> None:
        """启动 STT 会话
        
        Args:
            session_id: 会话 ID
            config: STT 配置
        """
        ...
    
    @abstractmethod
    async def send_audio(self, audio_chunk: bytes) -> None:
        """发送音频数据
        
        Args:
            audio_chunk: PCM 16bit 音频数据
        """
        ...
    
    @abstractmethod
    async def stop_session(self) -> None:
        """结束 STT 会话"""
        ...
    
    def on_partial(self, callback: PartialCallback) -> None:
        """注册部分结果回调"""
        self._on_partial = callback
    
    def on_final(self, callback: FinalCallback) -> None:
        """注册最终结果回调"""
        self._on_final = callback
    
    def on_error(self, callback: ErrorCallback) -> None:
        """注册错误回调"""
        self._on_error = callback
    
    def on_ready(self, callback: ReadyCallback) -> None:
        """注册就绪回调"""
        self._on_ready = callback
    
    def _emit_partial(self, result: SttResult) -> None:
        """发射部分结果"""
        if self._on_partial:
            self._on_partial(result)
    
    def _emit_final(self, result: SttResult) -> None:
        """发射最终结果"""
        if self._on_final:
            self._on_final(result)
    
    def _emit_error(self, error: Exception) -> None:
        """发射错误"""
        if self._on_error:
            self._on_error(error)
    
    def _emit_ready(self) -> None:
        """发射就绪信号"""
        if self._on_ready:
            self._on_ready()
