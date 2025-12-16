"""
编排引擎

协调多模态输入与 Agent 执行，实现端到端任务处理
"""

import uuid
import asyncio
from typing import AsyncIterator, Optional, Dict, Any, Callable

from .task import Task, TaskStatus, TaskResult, TaskContext, ExecutionStep, StepType
from .session import Session
from .events import PerceptionEvent, ModalityType, EventStage
from .trigger import TriggerEngine
from ..infra import get_logger, generate_trace_id

logger = get_logger(__name__)


class Orchestrator:
    """编排引擎 - 协调多模态输入与 Agent 执行"""
    
    def __init__(self, use_llm_trigger: bool = False):
        """
        Args:
            use_llm_trigger: 是否使用 LLM 进行触发判断
        """
        self.trigger = TriggerEngine(use_llm_judge=use_llm_trigger)
        self._agent = None
    
    def _get_agent(self):
        """懒加载 Agent"""
        if self._agent is None:
            from ..reasoning.agent import OmniAgent
            self._agent = OmniAgent()
        return self._agent
    
    async def execute(
        self,
        task: Task,
        input_stream: Optional[AsyncIterator[bytes]] = None,
        on_perception: Optional[Callable[[PerceptionEvent], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """执行端到端任务
        
        Args:
            task: 任务
            input_stream: 输入流（音频/图像等）
            on_perception: 感知事件回调
            on_thinking: 思考过程回调
            
        Yields:
            执行结果
        """
        logger.info(f"Task started | task_id={task.task_id} instruction='{task.instruction[:50]}...'")
        
        task.update_status(TaskStatus.PERCEIVING)
        step_id = 0
        
        try:
            # 判断输入模态
            if ModalityType.AUDIO in task.input_modalities and input_stream:
                # 音频输入：启动 STT 感知
                async for result in self._process_audio_stream(task, input_stream, on_perception):
                    yield result
                    
                    # 检查是否需要触发 Agent
                    if task.perception_buffer:
                        latest_event = task.perception_buffer[-1]
                        if await self.trigger.should_invoke_agent(task, latest_event):
                            task.update_status(TaskStatus.THINKING)
                            
                            # 调用 Agent
                            async for agent_result in self._invoke_agent(task, step_id, on_thinking):
                                yield agent_result
                                step_id += 1
                            
                            # 清空感知缓冲区
                            task.perception_buffer.clear()
                            task.update_status(TaskStatus.PERCEIVING)
            
            elif ModalityType.TEXT in task.input_modalities:
                # 文本输入：直接作为感知事件
                text_content = task.instruction  # 或从其他地方获取
                event = PerceptionEvent(
                    event_id=f"evt_{uuid.uuid4().hex[:8]}",
                    modality=ModalityType.TEXT,
                    stage=EventStage.FINAL,
                    content=text_content,
                )
                task.add_perception(event)
                
                if on_perception:
                    on_perception(event)
                
                yield {"type": "perception", "event": event.to_dict()}
                
                # 直接触发 Agent
                task.update_status(TaskStatus.THINKING)
                async for agent_result in self._invoke_agent(task, step_id, on_thinking):
                    yield agent_result
            
            else:
                # 无输入模态：直接调用 Agent（纯指令模式）
                task.update_status(TaskStatus.THINKING)
                async for agent_result in self._invoke_agent(task, step_id, on_thinking):
                    yield agent_result
            
            # 任务完成
            if task.status != TaskStatus.COMPLETED:
                task.update_status(TaskStatus.COMPLETED)
            
            logger.info(f"Task completed | task_id={task.task_id}")
            yield {"type": "complete", "task": task.to_dict()}
            
        except Exception as e:
            logger.error(f"Task failed | task_id={task.task_id} error={e}")
            task.fail(str(e))
            yield {"type": "error", "error": str(e)}
    
    async def _process_audio_stream(
        self,
        task: Task,
        audio_stream: AsyncIterator[bytes],
        on_perception: Optional[Callable[[PerceptionEvent], None]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理音频流"""
        from ..perception.stt import SttRegistry, SttConfig
        
        stt_service = SttRegistry.get_service("aliyun")
        result_queue: asyncio.Queue = asyncio.Queue()
        
        def on_partial(result):
            event = PerceptionEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                modality=ModalityType.AUDIO,
                stage=EventStage.PARTIAL,
                content=result.text,
                confidence=result.confidence if hasattr(result, 'confidence') else 0.0,
            )
            result_queue.put_nowait(("partial", event))
        
        def on_final(result):
            event = PerceptionEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                modality=ModalityType.AUDIO,
                stage=EventStage.FINAL,
                content=result.text,
                confidence=result.confidence if hasattr(result, 'confidence') else 1.0,
            )
            result_queue.put_nowait(("final", event))
        
        def on_ready():
            result_queue.put_nowait(("ready", None))
        
        def on_error(error):
            result_queue.put_nowait(("error", error))
        
        # 注册回调
        stt_service.on_partial(on_partial)
        stt_service.on_final(on_final)
        stt_service.on_ready(on_ready)
        stt_service.on_error(on_error)
        
        # 启动 STT 会话
        stt_config = SttConfig(
            model="paraformer-realtime-v2",
            language="zh-CN",
            sample_rate=16000,
            enable_punctuation=True,
        )
        await stt_service.start_session(task.task_id, stt_config)
        
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
                    event_type, event_data = await asyncio.wait_for(
                        result_queue.get(), 
                        timeout=0.1
                    )
                    
                    if event_type == "ready":
                        yield {"type": "stt_ready"}
                    elif event_type == "partial":
                        if on_perception:
                            on_perception(event_data)
                        yield {"type": "perception", "event": event_data.to_dict()}
                    elif event_type == "final":
                        task.add_perception(event_data)
                        if on_perception:
                            on_perception(event_data)
                        yield {"type": "perception", "event": event_data.to_dict()}
                    elif event_type == "error":
                        yield {"type": "error", "error": str(event_data)}
                        break
                        
                except asyncio.TimeoutError:
                    if send_task.done():
                        break
                    continue
            
            await send_task
            
        finally:
            try:
                await stt_service.stop_session()
            except:
                pass
    
    async def _invoke_agent(
        self,
        task: Task,
        step_id: int,
        on_thinking: Optional[Callable[[str], None]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """调用 Agent 进行推理"""
        from ..reasoning.llm import LlmRegistry, Message, MessageRole, LlmConfig
        
        # 构建 system prompt
        system_prompt = self._build_system_prompt(task)
        
        # 获取消息列表
        messages = task.get_messages()
        
        # 构建 LLM 消息
        llm_messages = [Message(role=MessageRole.SYSTEM, content=system_prompt)]
        for msg in messages:
            role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
            llm_messages.append(Message(role=role, content=msg.get("content", "")))
        
        # 创建执行步骤
        step = ExecutionStep(
            step_id=step_id,
            step_type=StepType.REASONING,
            trigger="perception_complete",
        )
        
        # 调用 LLM
        llm_service = LlmRegistry.get_service("qwen")
        config = LlmConfig(model="qwen-turbo", temperature=0.7, max_tokens=2048)
        
        full_content = ""
        async for chunk in llm_service.chat_stream(llm_messages, config):
            if chunk.delta:
                full_content += chunk.delta
                if on_thinking:
                    on_thinking(chunk.delta)
                yield {
                    "type": "thinking",
                    "delta": chunk.delta,
                    "step_id": step_id,
                }
        
        # 完成步骤
        step.observation = full_content
        step.finished_at = __import__('datetime').datetime.now()
        task.add_step(step)
        
        # 创建任务结果
        task.complete(TaskResult(
            content=full_content,
            messages=[
                {"role": "user", "content": task._format_perception()},
                {"role": "assistant", "content": full_content},
            ]
        ))
        
        yield {
            "type": "answer",
            "content": full_content,
            "step_id": step_id,
        }
    
    def _build_system_prompt(self, task: Task) -> str:
        """构建 system prompt"""
        modalities = ", ".join([m.value for m in task.input_modalities]) or "text"
        
        return f"""你是一个智能助手，正在执行以下任务：

## 任务指令
{task.instruction}

## 输入模态
{modalities}

## 执行规则
1. 根据任务指令理解用户意图
2. 基于感知到的内容做出响应
3. 给出清晰、有帮助的回答
"""


# 便捷函数
async def execute_task(
    instruction: str,
    input_stream: Optional[AsyncIterator[bytes]] = None,
    input_modalities: Optional[list] = None,
    context: Optional[TaskContext] = None,
) -> AsyncIterator[Dict[str, Any]]:
    """便捷函数：执行单次任务"""
    task = Task(
        task_id=f"task_{uuid.uuid4().hex[:12]}",
        instruction=instruction,
        input_modalities=input_modalities or [],
        context=context,
    )
    
    orchestrator = Orchestrator()
    async for result in orchestrator.execute(task, input_stream):
        yield result
