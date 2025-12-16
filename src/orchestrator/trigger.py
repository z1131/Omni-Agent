"""
触发引擎

决定何时触发 ReActAgent 进行推理
"""

from typing import Optional

from .task import Task
from .events import PerceptionEvent, ModalityType, EventStage
from ..infra import get_logger

logger = get_logger(__name__)


class TriggerEngine:
    """触发引擎 - 决定何时触发 Agent 推理"""
    
    def __init__(self, use_llm_judge: bool = False):
        """
        Args:
            use_llm_judge: 是否使用 LLM 进行智能判断
        """
        self.use_llm_judge = use_llm_judge
        self._llm_service = None
    
    async def should_invoke_agent(
        self,
        task: Task,
        event: PerceptionEvent,
    ) -> bool:
        """判断是否应该触发 Agent
        
        Args:
            task: 当前任务
            event: 新的感知事件
            
        Returns:
            是否触发 Agent
        """
        # 规则 1: 错误事件不触发
        if event.stage == EventStage.ERROR:
            return False
        
        # 规则 2: 文本输入直接触发
        if event.modality == ModalityType.TEXT and event.stage == EventStage.FINAL:
            logger.debug(f"Text input triggers agent | task_id={task.task_id}")
            return True
        
        # 规则 3: 语音识别到完整句子
        if event.modality == ModalityType.AUDIO and event.stage == EventStage.FINAL:
            if self.use_llm_judge:
                return await self._is_actionable_speech(task, event)
            else:
                # 简单规则：FINAL 事件且内容非空
                if event.content and len(event.content.strip()) > 0:
                    logger.debug(f"Audio final triggers agent | task_id={task.task_id}")
                    return True
        
        # 规则 4: 图像输入直接触发
        if event.modality == ModalityType.IMAGE and event.stage == EventStage.FINAL:
            logger.debug(f"Image input triggers agent | task_id={task.task_id}")
            return True
        
        return False
    
    async def _is_actionable_speech(
        self,
        task: Task,
        event: PerceptionEvent,
    ) -> bool:
        """使用 LLM 判断语音内容是否需要响应"""
        if self._llm_service is None:
            from ..reasoning.llm import LlmRegistry
            self._llm_service = LlmRegistry.get_service("qwen")
        
        prompt = f"""
用户指令: {task.instruction}

当前识别到的语音内容: {event.content}

请判断这段内容是否需要 Agent 做出响应？
- 如果是完整的问题或指令，返回 YES
- 如果是不完整的句子、背景噪音、无意义内容，返回 NO

只返回 YES 或 NO
"""
        
        try:
            from ..reasoning.llm import Message, MessageRole, LlmConfig
            messages = [Message(role=MessageRole.USER, content=prompt)]
            config = LlmConfig(model="qwen-turbo", temperature=0.1, max_tokens=10)
            
            response = await self._llm_service.chat(messages, config)
            result = response.content.strip().upper() == "YES"
            
            logger.debug(
                f"LLM judge result | task_id={task.task_id} "
                f"content='{event.content[:50]}...' result={result}"
            )
            return result
        except Exception as e:
            logger.error(f"LLM judge failed | error={e}")
            # 降级为简单规则
            return len(event.content.strip()) > 5
