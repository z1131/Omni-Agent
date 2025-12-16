"""
V1 API 路由

注意：realtime WebSocket 路由已移除，改用 gRPC 接口 (端口 50051)
"""

from fastapi import APIRouter

from .sessions import router as sessions_router
from .chat import router as chat_router
from .stt import router as stt_router
# WebSocket realtime 路由已废弃，改用 gRPC
# from .realtime import router as realtime_router

router = APIRouter(prefix="/api/v1")

router.include_router(sessions_router, tags=["sessions"])
router.include_router(chat_router, tags=["chat"])
router.include_router(stt_router, tags=["stt"])
# router.include_router(realtime_router, tags=["realtime"])
