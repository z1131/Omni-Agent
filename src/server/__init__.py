"""
Omni-Agent 接口层

提供 HTTP (FastAPI) 和 gRPC 两种接口
- http/: REST API 和 WebSocket
- grpc/: gRPC 双向流接口
"""

from .http.response import (
    ApiResponse,
    ErrorCode,
    success,
    error,
    invalid_param,
    session_not_found,
    internal_error,
)
from .grpc import GrpcServer

__all__ = [
    # HTTP
    'ApiResponse',
    'ErrorCode',
    'success',
    'error',
    'invalid_param',
    'session_not_found',
    'internal_error',
    # gRPC
    'GrpcServer',
]