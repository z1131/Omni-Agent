"""
LLM 服务抽象基类

按照 docs/01_FEATURES/认知层设计.md 实现
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """对话消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None           # 工具名称（tool 角色时使用）
    tool_call_id: Optional[str] = None   # 工具调用 ID
    tool_calls: Optional[List[Dict]] = None  # 工具调用列表（assistant 角色时使用）
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'role': self.role.value if isinstance(self.role, MessageRole) else self.role,
            'content': self.content
        }
        if self.name:
            result['name'] = self.name
        if self.tool_call_id:
            result['tool_call_id'] = self.tool_call_id
        if self.tool_calls:
            result['tool_calls'] = self.tool_calls
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建"""
        role = data.get('role', 'user')
        if isinstance(role, str):
            role = MessageRole(role)
        
        return cls(
            role=role,
            content=data.get('content', ''),
            name=data.get('name'),
            tool_call_id=data.get('tool_call_id'),
            tool_calls=data.get('tool_calls'),
            metadata=data.get('metadata')
        )


@dataclass
class LlmConfig:
    """LLM 配置"""
    model: str = "qwen-turbo"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048
    stop: Optional[List[str]] = None
    tools: Optional[List[Dict]] = None    # Function calling 工具定义
    tool_choice: Optional[str] = None     # auto, none, required
    
    # 扩展配置
    timeout: float = 60.0
    retry_times: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'model': self.model,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
        }
        if self.stop:
            result['stop'] = self.stop
        if self.tools:
            result['tools'] = self.tools
        if self.tool_choice:
            result['tool_choice'] = self.tool_choice
        return result


@dataclass
class TokenUsage:
    """Token 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }


@dataclass
class LlmResponse:
    """LLM 响应"""
    content: str
    finish_reason: str                     # stop, tool_calls, length, content_filter
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[TokenUsage] = None
    model: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'content': self.content,
            'finish_reason': self.finish_reason
        }
        if self.tool_calls:
            result['tool_calls'] = self.tool_calls
        if self.usage:
            result['usage'] = self.usage.to_dict()
        if self.model:
            result['model'] = self.model
        return result


@dataclass
class StreamChunk:
    """流式输出片段"""
    delta: str                              # 增量内容
    finish_reason: Optional[str] = None     # 结束原因
    tool_calls: Optional[List[Dict]] = None # 工具调用（增量）
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'delta': self.delta}
        if self.finish_reason:
            result['finish_reason'] = self.finish_reason
        if self.tool_calls:
            result['tool_calls'] = self.tool_calls
        return result


class LlmService(ABC):
    """LLM 服务抽象基类
    
    所有 LLM Provider 实现都需要继承此类
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider 名称"""
        ...
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        config: Optional[LlmConfig] = None
    ) -> LlmResponse:
        """同步对话（非流式）
        
        Args:
            messages: 消息列表
            config: LLM 配置
        
        Returns:
            LLM 响应
        """
        ...
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[LlmConfig] = None
    ) -> AsyncIterator[StreamChunk]:
        """流式对话
        
        Args:
            messages: 消息列表
            config: LLM 配置
        
        Yields:
            流式输出片段
        """
        ...
    
    def count_tokens(self, messages: List[Message]) -> int:
        """计算 token 数量（估算）
        
        子类可覆盖此方法使用精确的 tokenizer
        """
        total_chars = sum(len(m.content) for m in messages)
        # 中文约 2 字符/token，英文约 4 字符/token
        # 这里取一个折中值
        return total_chars // 2
    
    def _messages_to_dicts(self, messages: List[Message]) -> List[Dict]:
        """将 Message 列表转换为字典列表"""
        return [m.to_dict() for m in messages]
    
    def _ensure_config(self, config: Optional[LlmConfig]) -> LlmConfig:
        """确保配置存在"""
        return config or LlmConfig()
