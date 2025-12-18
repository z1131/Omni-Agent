"""
阿里云 DashScope 实时语音识别服务

基于 WebSocket 的流式语音转文字
"""

import os
import json
import asyncio
from typing import Optional
import time

from .base import SttService, SttConfig, SttResult, WordInfo
from ...infra import get_logger, get_metrics, EventStatus

logger = get_logger(__name__)
metrics = get_metrics()


class AliyunSttService(SttService):
    """阿里云 DashScope 实时语音识别
    
    基于 Paraformer 实时语音识别模型
    """
    
    # 静音帧：16kHz 采样率，16位 PCM，100ms 静音 = 3200 字节
    SILENCE_FRAME = bytes(3200)
    KEEPALIVE_INTERVAL = 10  # 每 10 秒发送一次静音帧保活
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化
        
        Args:
            api_key: DashScope API Key，默认从环境变量获取
        """
        super().__init__()
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            logger.warn("DASHSCOPE_API_KEY not set, STT service may not work")
        
        self._session_id: Optional[str] = None
        self._config: Optional[SttConfig] = None
        self._recognition = None
        self._running = False
        self._last_audio_time = 0.0
        self._keepalive_task: Optional[asyncio.Task] = None
    
    @property
    def provider_name(self) -> str:
        return "aliyun"
    
    async def start_session(self, session_id: str, config: SttConfig) -> None:
        """启动 STT 会话"""
        self._session_id = session_id
        self._config = config
        
        # 埋点
        metrics.track(
            "perception.stt", "stt_session_start",
            dimensions={"provider": "aliyun", "model": config.model}
        )
        
        try:
            import dashscope
            from dashscope.audio.asr import Recognition, RecognitionCallback
            
            dashscope.api_key = self.api_key
            
            # 创建回调处理器
            callback = self._create_callback()
            
            # 创建识别实例
            self._recognition = Recognition(
                model=config.model or 'paraformer-realtime-v2',
                format='pcm',
                sample_rate=config.sample_rate,
                callback=callback
            )
            
            # 启动识别
            self._recognition.start()
            self._running = True
            self._last_audio_time = time.time()
            
            # 启动保活任务
            self._keepalive_task = asyncio.create_task(self._keepalive_loop())
            
            logger.info("STT session started", session_id=session_id)
            self._emit_ready()
            
        except ImportError:
            error = ImportError("dashscope package not installed")
            logger.error("dashscope not installed", exc=error)
            self._emit_error(error)
            raise
        except Exception as e:
            logger.error("Failed to start STT session", exc=e)
            metrics.track(
                "perception.stt", "stt_error",
                status=EventStatus.ERROR,
                error={"code": type(e).__name__, "message": str(e)}
            )
            self._emit_error(e)
            raise
    
    def _create_callback(self):
        """创建 DashScope 回调处理器"""
        from dashscope.audio.asr import RecognitionCallback
        
        service = self  # 捕获 self 引用
        
        class SttCallback(RecognitionCallback):
            def on_open(self):
                logger.debug("STT WebSocket opened")
            
            def on_close(self):
                logger.debug("STT WebSocket closed")
            
            def on_event(self, result):
                """处理识别结果"""
                try:
                    sentence = result.get_sentence()
                    if sentence is None:
                        return
                    
                    text = sentence.get('text', '')
                    end_time = sentence.get('end_time')
                    is_final = end_time is not None and end_time > 0
                    
                    stt_result = SttResult(
                        text=text,
                        is_final=is_final,
                        confidence=sentence.get('confidence', 1.0),
                        start_time_ms=sentence.get('begin_time', 0),
                        end_time_ms=sentence.get('end_time', 0) or int(time.time() * 1000)
                    )
                    
                    if is_final:
                        service._emit_final(stt_result)
                        metrics.track(
                            "perception.stt", "stt_final",
                            metrics={
                                "latency_ms": stt_result.end_time_ms - stt_result.start_time_ms,
                                "char_count": len(text)
                            }
                        )
                    else:
                        service._emit_partial(stt_result)
                        metrics.track(
                            "perception.stt", "stt_partial",
                            metrics={"latency_ms": stt_result.end_time_ms - stt_result.start_time_ms}
                        )
                        
                except Exception as e:
                    logger.error("Error processing STT result", exc=e)
            
            def on_error(self, result):
                """处理错误"""
                error_msg = str(result)
                logger.error("STT error", error=error_msg)
                
                error = Exception(f"STT error: {error_msg}")
                service._emit_error(error)
                
                metrics.track(
                    "perception.stt", "stt_error",
                    status=EventStatus.ERROR,
                    error={"code": "STT_ERROR", "message": error_msg}
                )
            
            def on_complete(self):
                logger.debug("STT recognition completed")
        
        return SttCallback()
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        """发送音频数据"""
        if not self._running or self._recognition is None:
            # 会话已停止，静默忽略（避免竞态条件错误）
            logger.debug("STT session not running, ignoring audio chunk")
            return
        
        try:
            self._recognition.send_audio_frame(audio_chunk)
            self._last_audio_time = time.time()  # 更新最后音频时间
            
            metrics.track(
                "perception.stt", "stt_audio_received",
                metrics={"chunk_size": len(audio_chunk)}
            )
        except Exception as e:
            # 如果是 "Speech recognition has stopped" 错误，静默忽略
            if "has stopped" in str(e):
                logger.debug("STT already stopped, ignoring audio chunk")
                return
            logger.error("Failed to send audio", exc=e)
            self._emit_error(e)
            raise
    
    async def _keepalive_loop(self) -> None:
        """保活循环：定期发送静音帧防止空闲超时"""
        try:
            while self._running and self._recognition is not None:
                await asyncio.sleep(self.KEEPALIVE_INTERVAL)
                
                # 如果超过保活间隔没有收到音频，发送静音帧
                if self._running and self._recognition is not None:
                    elapsed = time.time() - self._last_audio_time
                    if elapsed >= self.KEEPALIVE_INTERVAL:
                        try:
                            self._recognition.send_audio_frame(self.SILENCE_FRAME)
                            logger.debug("Sent keepalive silence frame", 
                                       session_id=self._session_id, idle_seconds=elapsed)
                        except Exception as e:
                            logger.warn("Failed to send keepalive frame", exc=e)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Keepalive loop error", exc=e)
    
    async def transcribe_once(self, audio_data: bytes, config: SttConfig) -> str:
        """单次语音识别（非流式）
        
        Args:
            audio_data: 完整音频数据
            config: STT 配置
            
        Returns:
            识别出的文本
        """
        import dashscope
        from dashscope.audio.asr import Recognition
        
        dashscope.api_key = self.api_key
        
        results = []
        completed = asyncio.Event()
        error_msg = None
        
        class OnceCallback:
            def on_open(self):
                pass
            
            def on_close(self):
                pass
            
            def on_event(self, result):
                sentence = result.get_sentence()
                if sentence:
                    text = sentence.get('text', '')
                    end_time = sentence.get('end_time')
                    is_final = end_time is not None and end_time > 0
                    if is_final and text:
                        results.append(text)
            
            def on_error(self, result):
                nonlocal error_msg
                error_msg = str(result)
                completed.set()
            
            def on_complete(self):
                completed.set()
        
        try:
            recognition = Recognition(
                model=config.model or 'paraformer-realtime-v2',
                format='pcm',
                sample_rate=config.sample_rate or 16000,
                callback=OnceCallback()
            )
            
            recognition.start()
            
            # 分块发送音频（避免单次发送过大）
            chunk_size = 3200  # 100ms at 16kHz
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                recognition.send_audio_frame(chunk)
                await asyncio.sleep(0.01)  # 小延迟避免过快发送
            
            recognition.stop()
            
            # 等待完成
            try:
                await asyncio.wait_for(completed.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warn("Transcribe once timeout")
            
            if error_msg:
                raise Exception(f"STT error: {error_msg}")
            
            return " ".join(results)
            
        except Exception as e:
            logger.error("Transcribe once failed", exc=e)
            raise
    
    async def flush(self) -> None:
        """刷新当前音频缓冲"""
        # Aliyun SDK 不支持显式 flush，静默忽略
        pass
    
    async def stop_session(self) -> None:
        """结束 STT 会话"""
        # 先取消保活任务
        if self._keepalive_task is not None:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            self._keepalive_task = None
        
        if self._recognition is not None:
            try:
                self._recognition.stop()
            except Exception as e:
                logger.error("Error stopping STT", exc=e)
            finally:
                self._recognition = None
                self._running = False
        
        metrics.track("perception.stt", "stt_session_end")
        logger.info("STT session stopped", session_id=self._session_id)
        
        self._session_id = None
        self._config = None


class MockSttService(SttService):
    """Mock STT 服务（用于测试）"""
    
    def __init__(self):
        super().__init__()
        self._session_id = None
        self._running = False
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    async def start_session(self, session_id: str, config: SttConfig) -> None:
        self._session_id = session_id
        self._running = True
        logger.info("Mock STT session started", session_id=session_id)
        self._emit_ready()
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        if not self._running:
            raise RuntimeError("STT session not started")
        
        # 模拟延迟
        await asyncio.sleep(0.1)
        
        # 模拟返回结果
        result = SttResult(
            text="这是模拟的语音识别结果",
            is_final=True,
            confidence=0.95,
            start_time_ms=0,
            end_time_ms=int(time.time() * 1000)
        )
        self._emit_final(result)
    
    async def stop_session(self) -> None:
        self._running = False
        self._session_id = None
        logger.info("Mock STT session stopped")


# 服务注册
class SttRegistry:
    """STT 服务注册表"""
    
    _providers = {}
    _instances = {}
    
    @classmethod
    def register(cls, name: str, provider_class):
        cls._providers[name] = provider_class
    
    @classmethod
    def get_service(cls, provider: str = "aliyun", **kwargs) -> SttService:
        cls._register_builtin()
        
        if provider not in cls._providers:
            raise ValueError(f"Unknown STT provider: {provider}")
        
        return cls._providers[provider](**kwargs)
    
    @classmethod
    def _register_builtin(cls):
        if cls._providers:
            return
        cls._providers['aliyun'] = AliyunSttService
        cls._providers['dashscope'] = AliyunSttService
        cls._providers['mock'] = MockSttService
