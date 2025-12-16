"""
音频感知处理器
"""

import uuid
from typing import AsyncIterator
from datetime import datetime

from ..events import PerceptionEvent, ModalityType, EventStage


class AudioPerceptionHandler:
    """音频感知处理器"""
    
    async def process(
        self,
        audio_stream: AsyncIterator[bytes],
        session_id: str,
        provider: str = "aliyun",
        model: str = "paraformer-realtime-v2",
        language: str = "zh-CN",
        sample_rate: int = 16000,
    ) -> AsyncIterator[PerceptionEvent]:
        """处理音频流
        
        Args:
            audio_stream: 音频数据流
            session_id: 会话 ID
            provider: STT 服务提供商
            model: STT 模型
            language: 语言
            sample_rate: 采样率
            
        Yields:
            感知事件
        """
        from ...perception.stt import SttRegistry, SttConfig
        import asyncio
        
        stt_service = SttRegistry.get_service(provider)
        result_queue: asyncio.Queue = asyncio.Queue()
        
        def on_partial(result):
            event = PerceptionEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                modality=ModalityType.AUDIO,
                stage=EventStage.PARTIAL,
                content=result.text,
                confidence=getattr(result, 'confidence', 0.0),
                timestamp=datetime.now(),
            )
            result_queue.put_nowait(event)
        
        def on_final(result):
            event = PerceptionEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                modality=ModalityType.AUDIO,
                stage=EventStage.FINAL,
                content=result.text,
                confidence=getattr(result, 'confidence', 1.0),
                timestamp=datetime.now(),
            )
            result_queue.put_nowait(event)
        
        def on_error(error):
            event = PerceptionEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                modality=ModalityType.AUDIO,
                stage=EventStage.ERROR,
                content=str(error),
                confidence=0.0,
                timestamp=datetime.now(),
            )
            result_queue.put_nowait(event)
        
        # 注册回调
        stt_service.on_partial(on_partial)
        stt_service.on_final(on_final)
        stt_service.on_error(on_error)
        
        # 启动 STT 会话
        stt_config = SttConfig(
            model=model,
            language=language,
            sample_rate=sample_rate,
            enable_punctuation=True,
        )
        await stt_service.start_session(session_id, stt_config)
        
        try:
            # 启动音频发送协程
            async def send_audio():
                async for chunk in audio_stream:
                    await stt_service.send_audio(chunk)
                await stt_service.stop_session()
            
            send_task = asyncio.create_task(send_audio())
            
            # 处理结果
            while True:
                try:
                    event = await asyncio.wait_for(result_queue.get(), timeout=0.1)
                    yield event
                    
                    if event.stage == EventStage.ERROR:
                        break
                        
                except asyncio.TimeoutError:
                    if send_task.done():
                        # 等待队列中剩余的事件
                        while not result_queue.empty():
                            yield result_queue.get_nowait()
                        break
                    continue
            
            await send_task
            
        finally:
            try:
                await stt_service.stop_session()
            except:
                pass
