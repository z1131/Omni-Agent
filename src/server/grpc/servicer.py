"""
Omni-Agent gRPC Servicer 实现
"""
import asyncio
import uuid
from typing import AsyncIterator

from ...infra import get_logger, generate_trace_id

logger = get_logger(__name__)


class OmniAgentServicer:
    """Omni-Agent gRPC 服务实现"""
    
    def __init__(self):
        self._version = "1.0.0"
    
    async def StreamSTT(
        self, 
        request_iterator: AsyncIterator,
        context
    ) -> AsyncIterator:
        """
        STT 双向流
        客户端发送音频帧，服务端返回识别结果
        """
        from .generated import stt_pb2
        from ...perception.stt.aliyun import AliyunSttService
        
        trace_id = generate_trace_id()
        session_id = None
        stt_service = None
        result_queue: asyncio.Queue = asyncio.Queue()
        
        def on_partial(result):
            """处理中间识别结果"""
            result_queue.put_nowait(stt_pb2.SttResponse(
                result=stt_pb2.SttResult(
                    text=result.text,
                    is_final=False,
                    confidence=result.confidence or 0.0,
                    start_time_ms=result.start_time_ms or 0,
                    end_time_ms=result.end_time_ms or 0,
                )
            ))
        
        def on_final(result):
            """处理最终识别结果"""
            result_queue.put_nowait(stt_pb2.SttResponse(
                result=stt_pb2.SttResult(
                    text=result.text,
                    is_final=True,
                    confidence=result.confidence or 0.0,
                    start_time_ms=result.start_time_ms or 0,
                    end_time_ms=result.end_time_ms or 0,
                )
            ))
        
        def on_ready():
            """STT 准备就绪"""
            result_queue.put_nowait(stt_pb2.SttResponse(
                ready=stt_pb2.SttReady(
                    session_id=session_id,
                    message="STT ready"
                )
            ))
        
        def on_error(error):
            """处理错误"""
            result_queue.put_nowait(stt_pb2.SttResponse(
                error=stt_pb2.SttError(
                    code=5000,
                    message=str(error)
                )
            ))
        
        # 结果发送协程
        async def result_sender():
            """异步发送结果到客户端"""
            while True:
                try:
                    response = await asyncio.wait_for(result_queue.get(), timeout=0.05)
                    yield response
                except asyncio.TimeoutError:
                    yield None  # 超时返回 None，继续循环
                except asyncio.CancelledError:
                    break
        
        sender = result_sender()
        
        try:
            async for request in request_iterator:
                # 处理配置请求
                if request.HasField('config'):
                    config = request.config
                    session_id = config.session_id or f"stt_{uuid.uuid4().hex[:12]}"
                    
                    logger.info(
                        f"STT stream started | session_id={session_id} "
                        f"provider={config.provider} model={config.model} "
                        f"language={config.language} sample_rate={config.sample_rate}"
                    )
                    
                    # 创建 STT 服务并注册回调
                    from ...perception.stt.base import SttConfig
                    stt_service = AliyunSttService()
                    stt_service.on_partial(on_partial)
                    stt_service.on_final(on_final)
                    stt_service.on_ready(on_ready)
                    stt_service.on_error(on_error)
                    
                    stt_config = SttConfig(
                        model=config.model or 'paraformer-realtime-v2',
                        language=config.language or 'zh-CN',
                        sample_rate=config.sample_rate or 16000,
                        enable_punctuation=config.enable_punctuation,
                    )
                    await stt_service.start_session(session_id, stt_config)
                
                # 处理音频帧
                elif request.HasField('audio'):
                    if stt_service:
                        await stt_service.send_audio(request.audio.data)
                
                # 处理控制命令
                elif request.HasField('control'):
                    cmd = request.control.command
                    from .generated.stt_pb2 import SttControl
                    
                    if cmd == SttControl.END:
                        logger.info(f"STT stream ending | session_id={session_id}")
                        if stt_service:
                            await stt_service.stop_session()
                        
                        # 发送完成消息
                        yield stt_pb2.SttResponse(
                            complete=stt_pb2.SttComplete(
                                session_id=session_id,
                                message="STT complete"
                            )
                        )
                        break
                
                # 检查并发送待处理的结果
                while not result_queue.empty():
                    try:
                        response = result_queue.get_nowait()
                        yield response
                    except asyncio.QueueEmpty:
                        break
        
        except Exception as e:
            logger.error(f"STT stream error | session_id={session_id}", exc_info=e)
            yield stt_pb2.SttResponse(
                error=stt_pb2.SttError(
                    code=5000,
                    message=str(e)
                )
            )
        
        finally:
            if stt_service:
                try:
                    await stt_service.stop_session()
                except Exception as e:
                    logger.warning(f"Error stopping STT session | session_id={session_id}", exc_info=e)
            logger.info(f"STT stream closed | session_id={session_id}")
    
    async def StreamChat(
        self,
        request,
        context
    ) -> AsyncIterator:
        """
        LLM 流式调用
        客户端发送问题，服务端流式返回答案
        """
        from .generated import llm_pb2
        from ...reasoning.llm.qwen import QwenLlmService
        
        session_id = request.session_id or f"chat_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            f"Chat stream started | session_id={session_id} "
            f"provider={request.provider} model={request.model}"
        )
        
        try:
            # 构建消息列表
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            
            for msg in request.messages:
                messages.append({"role": msg.role, "content": msg.content})
            
            # 创建 LLM 服务
            llm_service = QwenLlmService()
            
            index = 0
            async for chunk in llm_service.stream_chat(
                messages=messages,
                model=request.model or "qwen-turbo",
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048,
            ):
                if chunk.get("type") == "delta":
                    yield llm_pb2.ChatResponse(
                        delta=llm_pb2.ChatDelta(
                            content=chunk.get("content", ""),
                            index=index
                        )
                    )
                    index += 1
                elif chunk.get("type") == "complete":
                    yield llm_pb2.ChatResponse(
                        complete=llm_pb2.ChatComplete(
                            finish_reason=chunk.get("finish_reason", "stop"),
                            prompt_tokens=chunk.get("prompt_tokens", 0),
                            completion_tokens=chunk.get("completion_tokens", 0),
                            total_tokens=chunk.get("total_tokens", 0),
                        )
                    )
        
        except Exception as e:
            logger.error(f"Chat stream error | session_id={session_id}", exc_info=e)
            yield llm_pb2.ChatResponse(
                error=llm_pb2.ChatError(
                    code=5000,
                    message=str(e)
                )
            )
        
        finally:
            logger.info(f"Chat stream closed | session_id={session_id}")
    
    async def HealthCheck(self, request, context):
        """健康检查"""
        from .generated import omni_agent_pb2
        
        return omni_agent_pb2.HealthResponse(
            healthy=True,
            version=self._version,
            metadata={
                "grpc": "enabled",
                "stt": "aliyun",
                "llm": "qwen",
            }
        )
