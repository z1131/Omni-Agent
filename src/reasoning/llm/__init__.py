"""
Omni-Agent LLM 服务层

提供统一的大模型调用接口，支持多 Provider 切换
"""

from .base import (
    LlmService,
    LlmConfig,
    Message,
    MessageRole,
    LlmResponse,
    StreamChunk,
)

from .registry import LlmRegistry

__all__ = [
    'LlmService',
    'LlmConfig',
    'Message',
    'MessageRole',
    'LlmResponse',
    'StreamChunk',
    'LlmRegistry',
]
