"""
对话 API
"""

import asyncio
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...response import success, error, session_not_found, ErrorCode
from .....orchestrator import get_session_manager
from .....reasoning.llm import LlmRegistry, Message, MessageRole, LlmConfig
from .....infra import get_logger, log_context, generate_trace_id

logger = get_logger(__name__)
router = APIRouter()


class MessageInput(BaseModel):
    """消息输入"""
    role: str = "user"
    content: str


class ChatRequestInput(BaseModel):
    """对话请求输入"""
    messages: List[MessageInput]
    config: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def chat(
    request: ChatRequestInput,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """非流式对话"""
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=x_session_id):
        try:
            # 验证会话
            session_manager = get_session_manager()
            session = session_manager.get_active(x_session_id)
            if not session:
                return session_not_found(x_session_id, trace_id).to_json_response()
            
            # 构建消息
            llm_messages = []
            if session.config.llm.system_message:
                llm_messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=session.config.llm.system_message
                ))
            
            for msg in request.messages:
                role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
                llm_messages.append(Message(role=role, content=msg.content))
            
            # 获取 LLM 服务
            llm_service = LlmRegistry.get_service(session.config.llm.provider)
            llm_config = LlmConfig(
                model=session.config.llm.model,
                temperature=session.config.llm.temperature,
                max_tokens=session.config.llm.max_tokens,
            )
            
            # 应用配置覆盖
            if request.config:
                if 'temperature' in request.config:
                    llm_config.temperature = request.config['temperature']
                if 'max_tokens' in request.config:
                    llm_config.max_tokens = request.config['max_tokens']
            
            # 调用 LLM
            response = await llm_service.chat(llm_messages, llm_config)
            session.stats.llm_requests += 1
            
            return success(
                data={
                    "message": {
                        "role": "assistant",
                        "content": response.content
                    },
                    "usage": response.usage.to_dict() if response.usage else None,
                    "finish_reason": response.finish_reason
                },
                trace_id=trace_id
            ).to_json_response()
            
        except ValueError as e:
            if "not found" in str(e).lower():
                return session_not_found(x_session_id, trace_id).to_json_response()
            return error(
                ErrorCode.INVALID_PARAM,
                str(e),
                trace_id=trace_id
            ).to_json_response()
        except Exception as e:
            logger.error("Chat error", exc=e)
            return error(
                ErrorCode.LLM_ERROR,
                str(e),
                trace_id=trace_id
            ).to_json_response()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequestInput,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """流式对话 (SSE)"""
    trace_id = x_trace_id or generate_trace_id()
    
    async def generate():
        import json
        with log_context(trace_id=trace_id, session_id=x_session_id):
            try:
                # 验证会话
                session_manager = get_session_manager()
                session = session_manager.get_active(x_session_id)
                if not session:
                    data = json.dumps({"code": 1003, "message": f"Session not found: {x_session_id}"})
                    yield f"event: error\ndata: {data}\n\n"
                    return
                
                # 构建消息
                llm_messages = []
                if session.config.llm.system_message:
                    llm_messages.append(Message(
                        role=MessageRole.SYSTEM,
                        content=session.config.llm.system_message
                    ))
                
                for msg in request.messages:
                    role = MessageRole.USER if msg.role == "user" else MessageRole.ASSISTANT
                    llm_messages.append(Message(role=role, content=msg.content))
                
                # 获取 LLM 服务
                llm_service = LlmRegistry.get_service(session.config.llm.provider)
                llm_config = LlmConfig(
                    model=session.config.llm.model,
                    temperature=session.config.llm.temperature,
                    max_tokens=session.config.llm.max_tokens,
                )
                
                # 应用配置覆盖
                if request.config:
                    if 'temperature' in request.config:
                        llm_config.temperature = request.config['temperature']
                    if 'max_tokens' in request.config:
                        llm_config.max_tokens = request.config['max_tokens']
                
                # 流式调用
                async for chunk in llm_service.chat_stream(llm_messages, llm_config):
                    if chunk.delta:
                        data = json.dumps({"content": chunk.delta}, ensure_ascii=False)
                        yield f"event: delta\ndata: {data}\n\n"
                    
                    if chunk.finish_reason:
                        data = json.dumps({"finish_reason": chunk.finish_reason})
                        yield f"event: done\ndata: {data}\n\n"
                
                session.stats.llm_requests += 1
                
            except ValueError as e:
                data = json.dumps({"code": 1003, "message": str(e)}, ensure_ascii=False)
                yield f"event: error\ndata: {data}\n\n"
            except Exception as e:
                logger.error("Stream error", exc=e)
                data = json.dumps({"code": 2002, "message": str(e)}, ensure_ascii=False)
                yield f"event: error\ndata: {data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Trace-ID": trace_id,
            "X-Session-ID": x_session_id,
        }
    )


def _escape_sse(text: str) -> str:
    """转义 SSE 数据中的特殊字符"""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
