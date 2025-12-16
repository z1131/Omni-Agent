"""
Agent 生命周期钩子

按照 docs/01_FEATURES/扩展机制设计.md 实现
提供 Agent 全生命周期的扩展点
"""

from typing import Dict, List, Any, Optional, Callable
from abc import ABC


class AgentHooks(ABC):
    """Agent 生命周期钩子基类
    
    领域项目可继承此类，覆盖相应方法实现自定义逻辑。
    所有方法都有默认实现（透传），按需覆盖即可。
    
    Usage:
        class InterviewHooks(AgentHooks):
            def on_message_received(self, message: dict) -> dict:
                # 自定义消息预处理
                return message
        
        agent = OmniAgent(hooks=InterviewHooks())
    """
    
    # ========== 消息处理 ==========
    
    def on_message_received(self, message: Dict) -> Dict:
        """用户消息接收时触发
        
        Args:
            message: {"role": "user", "content": "...", "metadata": {...}}
        
        Returns:
            处理后的消息，可修改 content 或添加 metadata
        
        Use cases:
            - 消息预处理（清洗、格式化）
            - 意图识别
            - 敏感词过滤
            - 多模态转换（如语音转文字后的处理）
        """
        return message
    
    def on_message_sent(self, message: Dict) -> Dict:
        """消息发送前触发
        
        Args:
            message: {"role": "assistant", "content": "...", "metadata": {...}}
        
        Returns:
            处理后的消息
        
        Use cases:
            - 响应格式化
            - 内容审核
            - 个性化调整
        """
        return message
    
    # ========== LLM 调用 ==========
    
    def on_before_llm_call(self, messages: List[Dict]) -> List[Dict]:
        """LLM 调用前触发
        
        Args:
            messages: 完整消息列表
        
        Returns:
            处理后的消息列表
        
        Use cases:
            - 注入上下文（RAG 检索结果）
            - 提示词增强
            - Few-shot 示例注入
            - 消息裁剪优化
        """
        return messages
    
    def on_after_llm_call(self, response: str) -> str:
        """LLM 调用后触发
        
        Args:
            response: LLM 原始响应文本
        
        Returns:
            处理后的响应
        
        Use cases:
            - 响应后处理
            - 格式转换
            - 结果校验
            - 置信度评估
        """
        return response
    
    def on_llm_stream_delta(self, delta: str) -> Optional[str]:
        """流式输出每个片段时触发
        
        Args:
            delta: 增量文本
        
        Returns:
            处理后的增量文本，返回 None 可跳过该片段
        
        Use cases:
            - 实时过滤
            - 流式转换
        """
        return delta
    
    # ========== 工具调用 ==========
    
    def on_before_tool_call(self, tool_name: str, params: Dict) -> Dict:
        """工具调用前触发
        
        Args:
            tool_name: 工具名称
            params: 调用参数
        
        Returns:
            处理后的参数
        
        Use cases:
            - 参数校验
            - 参数转换
            - 权限检查
            - 调用审计
        """
        return params
    
    def on_after_tool_call(self, tool_name: str, result: Any) -> Any:
        """工具调用后触发
        
        Args:
            tool_name: 工具名称
            result: 工具返回结果
        
        Returns:
            处理后的结果
        
        Use cases:
            - 结果转换
            - 错误处理
            - 结果缓存
        """
        return result
    
    def on_tool_error(self, tool_name: str, error: Exception) -> Optional[Any]:
        """工具调用出错时触发
        
        Args:
            tool_name: 工具名称
            error: 异常对象
        
        Returns:
            替代结果，返回 None 则继续抛出异常
        
        Use cases:
            - 错误恢复
            - 降级处理
        """
        return None
    
    # ========== 会话管理 ==========
    
    def on_session_start(self, session_id: str, metadata: Dict) -> None:
        """会话开始时触发
        
        Args:
            session_id: 会话 ID
            metadata: 会话元数据
        
        Use cases:
            - 初始化领域状态
            - 加载用户画像
            - 资源准备
        """
        pass
    
    def on_session_end(self, session_id: str, summary: Dict) -> None:
        """会话结束时触发
        
        Args:
            session_id: 会话 ID
            summary: 会话摘要信息
        
        Use cases:
            - 状态持久化
            - 会话总结
            - 资源清理
        """
        pass
    
    def on_turn_start(self, turn_id: int) -> None:
        """对话轮次开始时触发
        
        Args:
            turn_id: 轮次编号
        """
        pass
    
    def on_turn_end(self, turn_id: int, result: Dict) -> None:
        """对话轮次结束时触发
        
        Args:
            turn_id: 轮次编号
            result: 轮次结果
        """
        pass
    
    # ========== 错误处理 ==========
    
    def on_error(self, error: Exception, context: Dict) -> Optional[str]:
        """全局错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        
        Returns:
            用户友好的错误提示，返回 None 则使用默认处理
        
        Use cases:
            - 错误分类
            - 用户友好提示
            - 错误上报
        """
        return None


class CompositeHooks(AgentHooks):
    """组合多个钩子
    
    按顺序执行多个钩子的同名方法
    
    Usage:
        hooks = CompositeHooks([
            LoggingHooks(),
            AuditHooks(),
            InterviewHooks(),
        ])
        agent = OmniAgent(hooks=hooks)
    """
    
    def __init__(self, hooks: List[AgentHooks]):
        self._hooks = hooks
    
    def on_message_received(self, message: Dict) -> Dict:
        for hook in self._hooks:
            message = hook.on_message_received(message)
        return message
    
    def on_message_sent(self, message: Dict) -> Dict:
        for hook in self._hooks:
            message = hook.on_message_sent(message)
        return message
    
    def on_before_llm_call(self, messages: List[Dict]) -> List[Dict]:
        for hook in self._hooks:
            messages = hook.on_before_llm_call(messages)
        return messages
    
    def on_after_llm_call(self, response: str) -> str:
        for hook in self._hooks:
            response = hook.on_after_llm_call(response)
        return response
    
    def on_llm_stream_delta(self, delta: str) -> Optional[str]:
        for hook in self._hooks:
            delta = hook.on_llm_stream_delta(delta)
            if delta is None:
                return None
        return delta
    
    def on_before_tool_call(self, tool_name: str, params: Dict) -> Dict:
        for hook in self._hooks:
            params = hook.on_before_tool_call(tool_name, params)
        return params
    
    def on_after_tool_call(self, tool_name: str, result: Any) -> Any:
        for hook in self._hooks:
            result = hook.on_after_tool_call(tool_name, result)
        return result
    
    def on_tool_error(self, tool_name: str, error: Exception) -> Optional[Any]:
        for hook in self._hooks:
            result = hook.on_tool_error(tool_name, error)
            if result is not None:
                return result
        return None
    
    def on_session_start(self, session_id: str, metadata: Dict) -> None:
        for hook in self._hooks:
            hook.on_session_start(session_id, metadata)
    
    def on_session_end(self, session_id: str, summary: Dict) -> None:
        for hook in self._hooks:
            hook.on_session_end(session_id, summary)
    
    def on_turn_start(self, turn_id: int) -> None:
        for hook in self._hooks:
            hook.on_turn_start(turn_id)
    
    def on_turn_end(self, turn_id: int, result: Dict) -> None:
        for hook in self._hooks:
            hook.on_turn_end(turn_id, result)
    
    def on_error(self, error: Exception, context: Dict) -> Optional[str]:
        for hook in self._hooks:
            result = hook.on_error(error, context)
            if result is not None:
                return result
        return None


class LoggingHooks(AgentHooks):
    """日志记录钩子
    
    自动记录 Agent 生命周期事件
    """
    
    def __init__(self):
        from ..infra import get_logger
        self._logger = get_logger("agent.hooks")
    
    def on_message_received(self, message: Dict) -> Dict:
        self._logger.debug(
            "Message received",
            role=message.get('role'),
            content_length=len(message.get('content', ''))
        )
        return message
    
    def on_before_llm_call(self, messages: List[Dict]) -> List[Dict]:
        self._logger.debug("LLM call starting", message_count=len(messages))
        return messages
    
    def on_after_llm_call(self, response: str) -> str:
        self._logger.debug("LLM call completed", response_length=len(response))
        return response
    
    def on_before_tool_call(self, tool_name: str, params: Dict) -> Dict:
        self._logger.info("Tool call starting", tool_name=tool_name)
        return params
    
    def on_after_tool_call(self, tool_name: str, result: Any) -> Any:
        self._logger.info("Tool call completed", tool_name=tool_name)
        return result
    
    def on_session_start(self, session_id: str, metadata: Dict) -> None:
        self._logger.info("Session started", session_id=session_id)
    
    def on_session_end(self, session_id: str, summary: Dict) -> None:
        self._logger.info("Session ended", session_id=session_id)
    
    def on_error(self, error: Exception, context: Dict) -> Optional[str]:
        self._logger.error("Agent error", exc=error, **context)
        return None
