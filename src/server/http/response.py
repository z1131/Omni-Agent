"""
统一响应格式

定义 API 响应结构和错误码
"""

from typing import Any, Optional, Dict
from dataclasses import dataclass
from enum import IntEnum
from fastapi.responses import JSONResponse


class ErrorCode(IntEnum):
    """错误码定义"""
    SUCCESS = 0
    
    # 客户端错误 (1xxx)
    INVALID_PARAM = 1001
    AUTH_FAILED = 1002
    SESSION_NOT_FOUND = 1003
    SESSION_EXPIRED = 1004
    
    # 服务端错误 (2xxx)
    STT_ERROR = 2001
    LLM_ERROR = 2002
    TIMEOUT = 2003
    
    # 限制类错误 (3xxx)
    RATE_LIMIT = 3001
    QUOTA_EXCEEDED = 3002
    
    # 系统错误 (5xxx)
    INTERNAL_ERROR = 5000


ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.INVALID_PARAM: "Invalid parameter",
    ErrorCode.AUTH_FAILED: "Authentication failed",
    ErrorCode.SESSION_NOT_FOUND: "Session not found",
    ErrorCode.SESSION_EXPIRED: "Session expired",
    ErrorCode.STT_ERROR: "STT service error",
    ErrorCode.LLM_ERROR: "LLM service error",
    ErrorCode.TIMEOUT: "Request timeout",
    ErrorCode.RATE_LIMIT: "Rate limit exceeded",
    ErrorCode.QUOTA_EXCEEDED: "Quota exceeded",
    ErrorCode.INTERNAL_ERROR: "Internal server error",
}

HTTP_STATUS_MAP = {
    ErrorCode.SUCCESS: 200,
    ErrorCode.INVALID_PARAM: 400,
    ErrorCode.AUTH_FAILED: 401,
    ErrorCode.SESSION_NOT_FOUND: 404,
    ErrorCode.SESSION_EXPIRED: 410,
    ErrorCode.STT_ERROR: 502,
    ErrorCode.LLM_ERROR: 502,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.RATE_LIMIT: 429,
    ErrorCode.QUOTA_EXCEEDED: 429,
    ErrorCode.INTERNAL_ERROR: 500,
}


@dataclass
class ApiResponse:
    """API 响应结构"""
    code: int
    message: str
    data: Optional[Any] = None
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
            "data": self.data,
        }
        if self.trace_id:
            result["trace_id"] = self.trace_id
        return result
    
    def to_json_response(self) -> JSONResponse:
        status_code = HTTP_STATUS_MAP.get(ErrorCode(self.code), 200) if self.code in [e.value for e in ErrorCode] else 200
        return JSONResponse(content=self.to_dict(), status_code=status_code)


def success(data: Any = None, trace_id: Optional[str] = None) -> ApiResponse:
    """成功响应"""
    return ApiResponse(
        code=ErrorCode.SUCCESS,
        message="success",
        data=data,
        trace_id=trace_id
    )


def error(
    code: ErrorCode,
    message: Optional[str] = None,
    data: Any = None,
    trace_id: Optional[str] = None
) -> ApiResponse:
    """错误响应"""
    return ApiResponse(
        code=code,
        message=message or ERROR_MESSAGES.get(code, "Unknown error"),
        data=data,
        trace_id=trace_id
    )


def invalid_param(message: str, trace_id: Optional[str] = None) -> ApiResponse:
    """参数错误"""
    return error(ErrorCode.INVALID_PARAM, message, trace_id=trace_id)


def session_not_found(session_id: str, trace_id: Optional[str] = None) -> ApiResponse:
    """会话不存在"""
    return error(
        ErrorCode.SESSION_NOT_FOUND,
        f"Session not found: {session_id}",
        trace_id=trace_id
    )


def internal_error(message: str = None, trace_id: Optional[str] = None) -> ApiResponse:
    """内部错误"""
    return error(ErrorCode.INTERNAL_ERROR, message, trace_id=trace_id)
