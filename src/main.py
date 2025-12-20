"""
Omni-Agent 主应用入口

FastAPI 服务，提供对外 API
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .server.http.routes import v1_router
from .orchestrator import get_session_manager
from .infra import get_logger, setup_logging, log_context, generate_trace_id, init_nacos_registry, get_nacos_registry

# 初始化日志
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv('LOG_FORMAT', 'text')

# SLS 配置（从环境变量读取）
sls_config = None
if os.getenv('SLS_ENABLED', 'false').lower() == 'true':
    sls_config = {
        'enabled': True,
        'endpoint': os.getenv('SLS_ENDPOINT', 'cn-hangzhou.log.aliyuncs.com'),
        'project': os.getenv('SLS_PROJECT'),
        'logstore': os.getenv('SLS_LOGSTORE', 'omni-agent'),
        'access_key_id': os.getenv('SLS_ACCESS_KEY_ID'),
        'access_key_secret': os.getenv('SLS_ACCESS_KEY_SECRET'),
        'batch_size': int(os.getenv('SLS_BATCH_SIZE', '100')),
        'flush_interval_ms': int(os.getenv('SLS_FLUSH_INTERVAL_MS', '3000')),
    }

setup_logging(level=log_level, format=log_format, sls_config=sls_config)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Omni-Agent starting...")
    
    # 启动会话管理器
    session_manager = get_session_manager()
    await session_manager.start()
    
    # 启动 gRPC 服务器（如果启用）
    grpc_server = None
    grpc_port = int(os.getenv('GRPC_PORT', '50051'))
    grpc_enabled = os.getenv('GRPC_ENABLED', 'true').lower() == 'true'
    if grpc_enabled:
        from .server.grpc import GrpcServer
        grpc_server = GrpcServer(port=grpc_port)
        await grpc_server.start()
    
    # 注册到 Nacos（如果启用）
    nacos_registry = None
    nacos_enabled = os.getenv('NACOS_ENABLED', 'false').lower() == 'true'
    if nacos_enabled:
        nacos_server = os.getenv('NACOS_SERVER_ADDR', 'localhost:8848')
        nacos_namespace = os.getenv('NACOS_NAMESPACE', 'public')
        nacos_username = os.getenv('NACOS_USERNAME')
        nacos_password = os.getenv('NACOS_PASSWORD')
        nacos_service_name = os.getenv('NACOS_SERVICE_NAME', 'omni-agent')
        nacos_group = os.getenv('NACOS_GROUP', 'DEFAULT_GROUP')
        
        nacos_registry = init_nacos_registry(
            server_addr=nacos_server,
            namespace=nacos_namespace,
            username=nacos_username,
            password=nacos_password,
            service_name=nacos_service_name,
            service_port=grpc_port,
            group_name=nacos_group,
            metadata={
                'protocol': 'grpc',
                'version': '0.1.0'
            }
        )
        nacos_registry.register()
    
    logger.info("Omni-Agent started successfully")
    
    yield
    
    # 关闭时
    logger.info("Omni-Agent shutting down...")
    
    # 从 Nacos 注销
    if nacos_registry:
        nacos_registry.deregister()
    
    if grpc_server:
        await grpc_server.stop()
    await session_manager.stop()
    logger.info("Omni-Agent stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="Omni-Agent API",
    description="通用智能体内核 - 提供 STT、LLM、Agent 等 AI 能力",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "Internal server error",
            "data": None
        }
    )


# 请求日志中间件
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # 获取或生成 trace_id
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    
    with log_context(trace_id=trace_id):
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path
        )
        
        response = await call_next(request)
        
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code
        )
        
        # 添加 trace_id 到响应头
        response.headers["X-Trace-ID"] = trace_id
        
        return response


# 挂载 V1 API 路由
app.include_router(v1_router)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    session_manager = get_session_manager()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "sessions_count": session_manager.count()
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Omni-Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
