"""
会话管理 API
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, Field

from ...response import success, error, session_not_found, invalid_param, ErrorCode
from .....orchestrator import (
    get_session_manager, SessionConfig, SessionStatus
)
from .....infra import get_logger, log_context, generate_trace_id

logger = get_logger(__name__)
router = APIRouter()


class SttConfigInput(BaseModel):
    """STT 配置输入"""
    provider: str = "aliyun"
    model: str = "paraformer-realtime-v2"
    language: str = "zh-CN"
    sample_rate: int = 16000


class LlmConfigInput(BaseModel):
    """LLM 配置输入"""
    provider: str = "qwen"
    model: str = "qwen-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    system_message: Optional[str] = None


class SessionConfigInput(BaseModel):
    """会话配置输入"""
    stt: Optional[SttConfigInput] = None
    llm: Optional[LlmConfigInput] = None
    timeout_seconds: int = 3600


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    client_id: str = Field(..., description="客户端标识")
    config: Optional[SessionConfigInput] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    llm: Optional[Dict[str, Any]] = None
    stt: Optional[Dict[str, Any]] = None


@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """创建会话"""
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id):
        try:
            session_manager = get_session_manager()
            
            # 构建配置
            config = None
            if request.config:
                config_dict = request.config.model_dump(exclude_none=True)
                config = SessionConfig.from_dict(config_dict)
            
            # 创建会话
            session = session_manager.create_session(
                client_id=request.client_id,
                config=config,
                metadata=request.metadata
            )
            
            return success(
                data={
                    "session_id": session.session_id,
                    "trace_id": session.trace_id,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "config": session.config.to_dict(),
                    "endpoints": {
                        "chat": "/api/v1/chat",
                        "stream": "/api/v1/chat/stream",
                        "stt": "/api/v1/stt/recognize",
                    }
                },
                trace_id=trace_id
            ).to_json_response()
            
        except RuntimeError as e:
            logger.error("Failed to create session", exc=e)
            return error(
                ErrorCode.QUOTA_EXCEEDED,
                str(e),
                trace_id=trace_id
            ).to_json_response()
        except Exception as e:
            logger.error("Create session error", exc=e)
            return error(
                ErrorCode.INTERNAL_ERROR,
                str(e),
                trace_id=trace_id
            ).to_json_response()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """查询会话状态"""
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=session_id):
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)
        
        if not session:
            return session_not_found(session_id, trace_id).to_json_response()
        
        return success(
            data=session.to_dict(),
            trace_id=trace_id
        ).to_json_response()


@router.put("/sessions/{session_id}/config")
async def update_session_config(
    session_id: str,
    request: UpdateConfigRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """更新会话配置"""
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=session_id):
        session_manager = get_session_manager()
        
        config_updates = request.model_dump(exclude_none=True)
        session = session_manager.update_session_config(session_id, config_updates)
        
        if not session:
            return session_not_found(session_id, trace_id).to_json_response()
        
        return success(
            data={"config": session.config.to_dict()},
            trace_id=trace_id
        ).to_json_response()


@router.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """关闭会话"""
    trace_id = x_trace_id or generate_trace_id()
    
    with log_context(trace_id=trace_id, session_id=session_id):
        session_manager = get_session_manager()
        session = session_manager.close_session(session_id)
        
        if not session:
            return session_not_found(session_id, trace_id).to_json_response()
        
        duration_ms = int(
            (session.updated_at - session.created_at).total_seconds() * 1000
        )
        
        return success(
            data={
                "session_id": session_id,
                "duration_ms": duration_ms,
                "stats": session.stats.to_dict()
            },
            trace_id=trace_id
        ).to_json_response()


@router.get("/sessions")
async def list_sessions(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-ID")
):
    """列出会话"""
    trace_id = x_trace_id or generate_trace_id()
    
    session_manager = get_session_manager()
    
    status_enum = None
    if status:
        try:
            status_enum = SessionStatus(status)
        except ValueError:
            return invalid_param(
                f"Invalid status: {status}",
                trace_id
            ).to_json_response()
    
    sessions = session_manager.list_sessions(
        client_id=client_id,
        status=status_enum
    )
    
    return success(
        data={
            "sessions": [s.to_dict() for s in sessions],
            "total": len(sessions)
        },
        trace_id=trace_id
    ).to_json_response()
