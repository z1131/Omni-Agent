"""
LLM 服务注册表

管理和获取不同 Provider 的 LLM 服务实例
"""

from typing import Dict, Type, Optional, Any
from .base import LlmService


class LlmRegistry:
    """LLM 服务注册表
    
    Usage:
        # 获取服务
        service = LlmRegistry.get_service("qwen")
        
        # 注册新 Provider
        LlmRegistry.register("custom", CustomLlmService)
    """
    
    _providers: Dict[str, Type[LlmService]] = {}
    _instances: Dict[str, LlmService] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: Type[LlmService]) -> None:
        """注册 LLM Provider
        
        Args:
            name: Provider 名称
            provider_class: Provider 类
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get_service(
        cls,
        provider: str = "qwen",
        singleton: bool = True,
        **kwargs
    ) -> LlmService:
        """获取 LLM 服务实例
        
        Args:
            provider: Provider 名称
            singleton: 是否使用单例模式
            **kwargs: 传递给 Provider 构造函数的参数
        
        Returns:
            LLM 服务实例
        """
        if provider not in cls._providers:
            # 延迟注册内置 Provider
            cls._register_builtin_providers()
        
        if provider not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {provider}. "
                           f"Available: {list(cls._providers.keys())}")
        
        # 单例模式
        if singleton:
            cache_key = f"{provider}_{hash(frozenset(kwargs.items()))}"
            if cache_key not in cls._instances:
                cls._instances[cache_key] = cls._providers[provider](**kwargs)
            return cls._instances[cache_key]
        
        return cls._providers[provider](**kwargs)
    
    @classmethod
    def list_providers(cls) -> list:
        """列出所有已注册的 Provider"""
        cls._register_builtin_providers()
        return list(cls._providers.keys())
    
    @classmethod
    def _register_builtin_providers(cls) -> None:
        """注册内置 Provider"""
        if cls._providers:
            return
        
        # Qwen (DashScope)
        from .qwen import QwenLlmService
        cls._providers['qwen'] = QwenLlmService
        cls._providers['dashscope'] = QwenLlmService
        cls._providers['tongyi'] = QwenLlmService


# 便捷函数
def get_llm_service(provider: str = "qwen", **kwargs) -> LlmService:
    """获取 LLM 服务实例（便捷函数）"""
    return LlmRegistry.get_service(provider, **kwargs)
