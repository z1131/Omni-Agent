"""
Omni-Agent gRPC Servicer 实现
"""
import asyncio
import uuid
from typing import AsyncIterator

from ...infra import get_logger, generate_trace_id
from ...reasoning.llm.base import Message, MessageRole, LlmConfig

logger = get_logger(__name__)



def _convert_messages(messages: list) -> list:
    """将字典消息列表转换为 Message 对象列表"""
    return [
        Message(
            role=MessageRole(msg["role"]) if msg["role"] in ["system", "user", "assistant"] else MessageRole.USER,
            content=msg["content"]
        )
        for msg in messages
    ]

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
            
            # 转换消息为 Message 对象
            typed_messages = _convert_messages(messages)
            
            # 构建 LLM 配置
            llm_config = LlmConfig(
                model=request.model or "qwen-turbo",
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens or 2048,
            )
            
            # 创建 LLM 服务并调用
            llm_service = QwenLlmService()
            index = 0
            
            async for chunk in llm_service.chat_stream(typed_messages, llm_config):
                if chunk.delta:
                    yield llm_pb2.ChatResponse(
                        delta=llm_pb2.ChatDelta(
                            content=chunk.delta,
                            index=index
                        )
                    )
                    index += 1
                
                if chunk.finish_reason and chunk.finish_reason != "null":
                    yield llm_pb2.ChatResponse(
                        complete=llm_pb2.ChatComplete(
                            finish_reason=chunk.finish_reason,
                            prompt_tokens=0,
                            completion_tokens=0,
                            total_tokens=0,
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
    
    async def Process(self, request, context):
        """
        统一多模态处理（非流式）
        支持 text + audio + image 组合输入
        """
        from .generated import multimodal_pb2
        from ...perception.stt.aliyun import AliyunSttService
        from ...reasoning.llm.qwen import QwenLlmService
        import time
        
        start_time = time.time()
        session_id = request.session_id or f"mm_{uuid.uuid4().hex[:12]}"
        config = request.config
        
        logger.info(f"MultiModal Process started | session_id={session_id} inputs={len(request.inputs)}")
        
        try:
            # 1. 收集所有输入
            text_inputs = []
            audio_inputs = []
            transcribed_text = ""
            
            for inp in request.inputs:
                if inp.HasField('text'):
                    text_inputs.append({
                        "role": inp.text.role or "user",
                        "content": inp.text.content
                    })
                elif inp.HasField('audio'):
                    audio_inputs.append(inp.audio)
            
            # 2. 处理音频输入（STT）
            if audio_inputs:
                stt_service = AliyunSttService()
                from ...perception.stt.base import SttConfig
                
                stt_config = SttConfig(
                    model=config.stt_model or 'paraformer-realtime-v2',
                    language=config.language or 'zh-CN',
                    sample_rate=16000,
                    enable_punctuation=True,
                )
                
                # 合并所有音频数据
                all_audio = b''.join([a.data for a in audio_inputs])
                
                # 单次识别
                transcribed_text = await stt_service.transcribe_once(all_audio, stt_config)
                logger.info(f"STT result | session_id={session_id} text={transcribed_text[:50]}...")
                
                # 将转写结果添加到消息中
                if transcribed_text:
                    text_inputs.append({"role": "user", "content": transcribed_text})
            
            # 3. 构建 LLM 消息
            messages = []
            if config.system_prompt:
                messages.append({"role": "system", "content": config.system_prompt})
            messages.extend(text_inputs)
            
            if not messages or all(m["role"] == "system" for m in messages):
                return multimodal_pb2.MultiModalResponse(
                    session_id=session_id,
                    outputs=[],
                    metadata=multimodal_pb2.ProcessingMetadata(
                        finish_reason="no_input",
                        latency_ms=int((time.time() - start_time) * 1000)
                    )
                )
            
            # 4. 调用 LLM
            typed_messages = _convert_messages(messages)
            
            llm_config = LlmConfig(
                model=config.llm_model or "qwen-turbo",
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 2048,
            )
            
            llm_service = QwenLlmService()
            full_response = ""
            
            async for chunk in llm_service.chat_stream(typed_messages, llm_config):
                if chunk.delta:
                    full_response += chunk.delta
            
            # 5. 构建响应
            latency_ms = int((time.time() - start_time) * 1000)
            
            return multimodal_pb2.MultiModalResponse(
                session_id=session_id,
                outputs=[
                    multimodal_pb2.ModalityOutput(
                        text=multimodal_pb2.TextOutput(
                            content=full_response,
                            role="assistant"
                        )
                    )
                ],
                metadata=multimodal_pb2.ProcessingMetadata(
                    finish_reason="stop",
                    prompt_tokens=0,  # TODO: 从 LLM 响应中获取实际值
                    completion_tokens=0,  # TODO: 从 LLM 响应中获取实际值
                    transcribed_text=transcribed_text,
                    latency_ms=latency_ms
                )
            )
        
        except Exception as e:
            logger.error(f"MultiModal Process error | session_id={session_id}", exc_info=e)
            return multimodal_pb2.MultiModalResponse(
                session_id=session_id,
                outputs=[],
                metadata=multimodal_pb2.ProcessingMetadata(
                    finish_reason="error",
                    latency_ms=int((time.time() - start_time) * 1000)
                )
            )
    
    async def ProcessStream(
        self,
        request_iterator: AsyncIterator,
        context
    ) -> AsyncIterator:
        """
        流式多模态处理 - 实时对话辅助模式
        
        支持两种模式：
        1. 自动触发模式：STT 识别到句子结束时自动触发 LLM 生成（适用于面试辅助等场景）
        2. 手动触发模式：用户发送 END_AUDIO 后触发 LLM 生成（传统模式）
        
        默认使用自动触发模式。
        """
        from .generated import multimodal_pb2
        from ...perception.stt.aliyun import AliyunSttService
        from ...reasoning.llm.qwen import QwenLlmService
        from ...perception.stt.base import SttConfig
        import time
        
        start_time = time.time()
        session_id = None
        config = None
        initial_inputs = []
        stt_service = None
        audio_ended = False
        
        # 用于通信的队列
        result_queue: asyncio.Queue = asyncio.Queue()
        # 待处理的 STT 句子队列（用于自动触发 LLM）
        pending_sentences: asyncio.Queue = asyncio.Queue()
        # 当前正在进行的 LLM 生成任务
        current_llm_task: asyncio.Task = None
        # 对话历史（用于多轮对话）
        conversation_history = []
        # 回答计数
        answer_index = 0
        
        def on_partial(result):
            """STT 中间结果 - 实时显示正在识别的内容"""
            result_queue.put_nowait(("stt_partial", result.text, result.confidence or 0.0))
        
        def on_final(result):
            """STT 最终结果 - 句子识别完成，触发 LLM 生成"""
            result_queue.put_nowait(("stt_final", result.text, result.confidence or 0.0))
            # 将完整句子放入待处理队列
            if result.text.strip():
                pending_sentences.put_nowait(result.text.strip())
        
        def on_ready():
            """STT 准备就绪"""
            result_queue.put_nowait(("ready", session_id, "Ready for audio"))
        
        def on_error(error):
            """STT 错误"""
            result_queue.put_nowait(("error", str(error), None))
        
        async def generate_answer(sentence: str, ans_idx: int) -> AsyncIterator:
            """为识别到的句子生成回答"""
            nonlocal conversation_history
            
            logger.info(f"Auto-triggering LLM | session_id={session_id} sentence='{sentence[:50]}...' answer_idx={ans_idx}")
            
            # 构建消息
            messages = []
            if config and config.system_prompt:
                messages.append({"role": "system", "content": config.system_prompt})
            
            # 添加对话历史
            messages.extend(conversation_history)
            
            # 添加当前句子
            messages.append({"role": "user", "content": sentence})
            
            # 调用 LLM
            typed_messages = _convert_messages(messages)
            llm_config = LlmConfig(
                model=config.llm_model or "qwen-turbo" if config else "qwen-turbo",
                temperature=config.temperature or 0.7 if config else 0.7,
                max_tokens=config.max_tokens or 2048 if config else 2048,
            )
            
            llm_service = QwenLlmService()
            full_response = ""
            token_index = 0
            
            async for chunk in llm_service.chat_stream(typed_messages, llm_config):
                if chunk.delta:
                    full_response += chunk.delta
                    yield multimodal_pb2.MultiModalStreamResponse(
                        llm=multimodal_pb2.StreamLlmFrame(
                            delta=chunk.delta,
                            index=token_index
                        )
                    )
                    token_index += 1
            
            # 更新对话历史
            conversation_history.append({"role": "user", "content": sentence})
            conversation_history.append({"role": "assistant", "content": full_response})
            
            # 发送本轮回答完成事件
            yield multimodal_pb2.MultiModalStreamResponse(
                complete=multimodal_pb2.StreamCompleteFrame(
                    finish_reason="sentence_complete",
                    metadata=multimodal_pb2.ProcessingMetadata(
                        transcribed_text=sentence,
                        latency_ms=int((time.time() - start_time) * 1000)
                    )
                )
            )
            
            logger.info(f"Answer generated | session_id={session_id} answer_idx={ans_idx} response_len={len(full_response)}")
        
        try:
            async for request in request_iterator:
                # 处理开始帧
                if request.HasField('start'):
                    start_frame = request.start
                    session_id = start_frame.session_id or f"mms_{uuid.uuid4().hex[:12]}"
                    config = start_frame.config
                    initial_inputs = list(start_frame.initial_inputs)
                    
                    logger.info(f"ProcessStream started (auto-trigger mode) | session_id={session_id}")
                    
                    # 创建 STT 服务
                    stt_service = AliyunSttService()
                    stt_service.on_partial(on_partial)
                    stt_service.on_final(on_final)
                    stt_service.on_ready(on_ready)
                    stt_service.on_error(on_error)
                    
                    stt_config = SttConfig(
                        model=config.stt_model or 'paraformer-realtime-v2',
                        language=config.language or 'zh-CN',
                        sample_rate=16000,
                        enable_punctuation=True,
                    )
                    await stt_service.start_session(session_id, stt_config)
                    
                    # 发送就绪事件
                    yield multimodal_pb2.MultiModalStreamResponse(
                        ready=multimodal_pb2.StreamReadyFrame(
                            session_id=session_id,
                            message="Ready for audio (auto-trigger mode)"
                        )
                    )
                
                # 处理音频帧
                elif request.HasField('audio'):
                    if stt_service:
                        await stt_service.send_audio(request.audio.data)
                    
                    # 处理 STT 结果队列
                    while not result_queue.empty():
                        try:
                            event = result_queue.get_nowait()
                            event_type, text, confidence = event
                            
                            if event_type == "stt_partial":
                                yield multimodal_pb2.MultiModalStreamResponse(
                                    stt=multimodal_pb2.StreamSttFrame(
                                        text=text,
                                        is_final=False,
                                        confidence=confidence or 0.0
                                    )
                                )
                            elif event_type == "stt_final":
                                yield multimodal_pb2.MultiModalStreamResponse(
                                    stt=multimodal_pb2.StreamSttFrame(
                                        text=text,
                                        is_final=True,
                                        confidence=confidence or 0.0
                                    )
                                )
                            elif event_type == "error":
                                yield multimodal_pb2.MultiModalStreamResponse(
                                    error=multimodal_pb2.StreamErrorFrame(
                                        code=5000,
                                        message=text,
                                        recoverable=False
                                    )
                                )
                        except asyncio.QueueEmpty:
                            break
                    
                    # 检查是否有新的句子需要生成回答（自动触发模式）
                    while not pending_sentences.empty():
                        try:
                            sentence = pending_sentences.get_nowait()
                            # 为这个句子生成回答
                            async for response in generate_answer(sentence, answer_index):
                                yield response
                            answer_index += 1
                        except asyncio.QueueEmpty:
                            break
                
                # 处理控制帧
                elif request.HasField('control'):
                    cmd = request.control.command
                    
                    if cmd == multimodal_pb2.StreamControlFrame.FLUSH:
                        if stt_service:
                            await stt_service.flush()
                    
                    elif cmd == multimodal_pb2.StreamControlFrame.END_AUDIO:
                        # 音频结束
                        audio_ended = True
                        
                        if stt_service:
                            await stt_service.stop_session()
                            stt_service = None
                        
                        # 等待最后的 STT 结果
                        await asyncio.sleep(0.05)
                        
                        # 处理剩余的 STT 结果
                        while not result_queue.empty():
                            try:
                                event = result_queue.get_nowait()
                                event_type, text, confidence = event
                                if event_type in ("stt_partial", "stt_final"):
                                    yield multimodal_pb2.MultiModalStreamResponse(
                                        stt=multimodal_pb2.StreamSttFrame(
                                            text=text,
                                            is_final=(event_type == "stt_final"),
                                            confidence=confidence or 0.0
                                        )
                                    )
                            except asyncio.QueueEmpty:
                                break
                        
                        # 处理剩余的待回答句子
                        while not pending_sentences.empty():
                            try:
                                sentence = pending_sentences.get_nowait()
                                async for response in generate_answer(sentence, answer_index):
                                    yield response
                                answer_index += 1
                            except asyncio.QueueEmpty:
                                break
                        
                        # 发送最终完成事件
                        yield multimodal_pb2.MultiModalStreamResponse(
                            complete=multimodal_pb2.StreamCompleteFrame(
                                finish_reason="stop",
                                metadata=multimodal_pb2.ProcessingMetadata(
                                    latency_ms=int((time.time() - start_time) * 1000)
                                )
                            )
                        )
                        break
                    
                    elif cmd == multimodal_pb2.StreamControlFrame.CANCEL:
                        logger.info(f"ProcessStream cancelled | session_id={session_id}")
                        break
        
        except Exception as e:
            logger.error(f"ProcessStream error | session_id={session_id}", exc_info=e)
            yield multimodal_pb2.MultiModalStreamResponse(
                error=multimodal_pb2.StreamErrorFrame(
                    code=5000,
                    message=str(e),
                    recoverable=False
                )
            )
        
        finally:
            if stt_service:
                try:
                    await stt_service.stop_session()
                except Exception:
                    pass
            logger.info(f"ProcessStream closed | session_id={session_id} total_answers={answer_index}")
    
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
                "multimodal": "enabled",
            }
        )
