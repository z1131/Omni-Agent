"""
阿里云 Qwen (通义千问) LLM 服务实现

基于 DashScope API
"""

import os
import json
import time
from typing import List, Dict, Any, AsyncIterator, Optional

from .base import (
    LlmService, LlmConfig, Message, MessageRole,
    LlmResponse, StreamChunk, TokenUsage
)
from ...infra import get_logger, get_metrics, EventStatus

logger = get_logger(__name__)
metrics = get_metrics()


class QwenLlmService(LlmService):
    """阿里云 Qwen 大模型服务
    
    支持 DashScope API，包括流式和非流式调用
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化
        
        Args:
            api_key: DashScope API Key，默认从环境变量 DASHSCOPE_API_KEY 获取
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            logger.warn("DASHSCOPE_API_KEY not set, Qwen service may not work")
        
        self._init_dashscope()
    
    def _init_dashscope(self):
        """初始化 DashScope SDK"""
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self._dashscope = dashscope
        except ImportError:
            logger.error("dashscope package not installed, run: pip install dashscope")
            self._dashscope = None
    
    @property
    def provider_name(self) -> str:
        return "qwen"
    
    async def chat(
        self,
        messages: List[Message],
        config: Optional[LlmConfig] = None
    ) -> LlmResponse:
        """同步对话"""
        config = self._ensure_config(config)
        
        # 埋点：调用开始
        metrics.track(
            "llm.call", "llm_call_start",
            dimensions={"model": config.model, "streaming": "false", "provider": "qwen"}
        )
        
        start_time = time.time()
        
        try:
            from dashscope import Generation
            
            # 构建请求参数
            request_params = {
                'model': config.model,
                'messages': self._messages_to_dicts(messages),
                'temperature': config.temperature,
                'top_p': config.top_p,
                'max_tokens': config.max_tokens,
                'result_format': 'message'
            }
            
            if config.stop:
                request_params['stop'] = config.stop
            if config.tools:
                request_params['tools'] = config.tools
            if config.tool_choice:
                request_params['tool_choice'] = config.tool_choice
            
            # 调用 API
            response = Generation.call(**request_params)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 检查响应
            if response.status_code != 200:
                error_msg = f"Qwen API error: {response.code} - {response.message}"
                logger.error(error_msg, status_code=response.status_code)
                metrics.track(
                    "llm.call", "llm_call_error",
                    status=EventStatus.ERROR,
                    dimensions={"model": config.model, "error_code": str(response.code)},
                    duration_ms=duration_ms
                )
                raise Exception(error_msg)
            
            # 解析响应
            choice = response.output.choices[0]
            message = choice.message
            
            # 构建返回
            result = LlmResponse(
                content=message.get('content', '') or '',
                finish_reason=choice.finish_reason,
                tool_calls=message.get('tool_calls'),
                usage=TokenUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                ),
                model=config.model
            )
            
            # 埋点：调用完成
            metrics.track(
                "llm.call", "llm_call_complete",
                dimensions={"model": config.model, "streaming": "false", "provider": "qwen"},
                duration_ms=duration_ms,
                metrics={
                    "tokens_in": result.usage.prompt_tokens,
                    "tokens_out": result.usage.completion_tokens
                }
            )
            
            logger.info(
                "LLM call completed",
                model=config.model,
                duration_ms=duration_ms,
                tokens_in=result.usage.prompt_tokens,
                tokens_out=result.usage.completion_tokens
            )
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            metrics.track(
                "llm.call", "llm_call_error",
                status=EventStatus.ERROR,
                dimensions={"model": config.model, "error_code": type(e).__name__},
                duration_ms=duration_ms,
                error={"code": type(e).__name__, "message": str(e)}
            )
            logger.error("LLM call failed", exc=e, model=config.model)
            raise
    
    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[LlmConfig] = None
    ) -> AsyncIterator[StreamChunk]:
        """流式对话"""
        config = self._ensure_config(config)
        
        # 埋点：调用开始
        metrics.track(
            "llm.call", "llm_call_start",
            dimensions={"model": config.model, "streaming": "true", "provider": "qwen"}
        )
        
        start_time = time.time()
        first_token_time = None
        total_content = ""
        finish_reason = None
        
        try:
            from dashscope import Generation
            
            # 构建请求参数
            request_params = {
                'model': config.model,
                'messages': self._messages_to_dicts(messages),
                'temperature': config.temperature,
                'top_p': config.top_p,
                'max_tokens': config.max_tokens,
                'result_format': 'message',
                'stream': True,
                'incremental_output': True  # 增量输出
            }
            
            if config.stop:
                request_params['stop'] = config.stop
            if config.tools:
                request_params['tools'] = config.tools
            if config.tool_choice:
                request_params['tool_choice'] = config.tool_choice
            
            # 流式调用
            responses = Generation.call(**request_params)
            
            for response in responses:
                if response.status_code != 200:
                    error_msg = f"Qwen stream error: {response.code} - {response.message}"
                    logger.error(error_msg)
                    metrics.track(
                        "llm.call", "llm_call_error",
                        status=EventStatus.ERROR,
                        dimensions={"model": config.model, "error_code": str(response.code)}
                    )
                    raise Exception(error_msg)
                
                choice = response.output.choices[0]
                message = choice.message
                delta = message.get('content', '') or ''
                
                # 首 token 计时
                if delta and first_token_time is None:
                    first_token_time = time.time()
                    ttft_ms = int((first_token_time - start_time) * 1000)
                    metrics.track(
                        "llm.stream", "stream_first_token",
                        dimensions={"model": config.model, "provider": "qwen"},
                        metrics={"ttft_ms": ttft_ms}
                    )
                
                total_content += delta
                
                # 检查结束
                if choice.finish_reason and choice.finish_reason != 'null':
                    finish_reason = choice.finish_reason
                
                yield StreamChunk(
                    delta=delta,
                    finish_reason=finish_reason,
                    tool_calls=message.get('tool_calls')
                )
            
            # 埋点：流式完成
            duration_ms = int((time.time() - start_time) * 1000)
            metrics.track(
                "llm.call", "llm_call_complete",
                dimensions={"model": config.model, "streaming": "true", "provider": "qwen"},
                duration_ms=duration_ms,
                metrics={"content_length": len(total_content)}
            )
            
            logger.info(
                "LLM stream completed",
                model=config.model,
                duration_ms=duration_ms,
                content_length=len(total_content)
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            metrics.track(
                "llm.call", "llm_call_error",
                status=EventStatus.ERROR,
                dimensions={"model": config.model, "error_code": type(e).__name__},
                duration_ms=duration_ms,
                error={"code": type(e).__name__, "message": str(e)}
            )
            logger.error("LLM stream failed", exc=e, model=config.model)
            raise
    
    def count_tokens(self, messages: List[Message]) -> int:
        """计算 token 数量
        
        Qwen 使用 qwen tokenizer，这里使用简单估算
        """
        total_chars = sum(len(m.content) for m in messages)
        # Qwen 中文约 1.5-2 字符/token
        return int(total_chars / 1.8)
