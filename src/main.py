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
from .infra import (
    get_logger, setup_logging, log_context, generate_trace_id,
    init_nacos_registry, get_nacos_registry,
    init_nacos_config, get_nacos_config, get_config_value
)


def _get_config(key_path: str, default=None, data_id: str = None):
    """
    统一配置获取函数
    优先从 Nacos 读取，如果 Nacos 未启用或配置不存在，则从环境变量读取
    
    Args:
        key_path: 配置路径，如 "llm.dashscope-api-key"
        default: 默认值
        data_id: Nacos 配置 ID，默认为 omni-agent.yaml
    """
    nacos_config = get_nacos_config()
    
    if nacos_config:
        # 先尝试 omni-agent.yaml
        if data_id is None:
            value = nacos_config.get_value("omni-agent.yaml", key_path)
            if value is not None:
                return value
            # 再尝试 common.yaml
            value = nacos_config.get_value("common.yaml", key_path)
            if value is not None:
                return value
        else:
            value = nacos_config.get_value(data_id, key_path)
            if value is not None:
                return value
    
    return default


def _init_config_from_nacos_or_env():
    """初始化配置，优先使用 Nacos，否则使用环境变量"""
    nacos_config = get_nacos_config()
    
    if nacos_config:
        # 从 Nacos 读取配置
        omni_config = nacos_config.get_config("omni-agent.yaml")
        common_config = nacos_config.get_config("common.yaml")
        
        # 日志配置
        log_level = omni_config.get("logging", {}).get("level", "INFO")
        log_format = omni_config.get("logging", {}).get("format", "text")
        
        # SLS 配置（合并 common 和 omni-agent）
        common_sls = common_config.get("sls", {})
        omni_sls = omni_config.get("sls", {})
        
        sls_config = None
        sls_enabled = omni_sls.get("enabled", common_sls.get("enabled", False))
        if sls_enabled:
            sls_config = {
                'enabled': True,
                'endpoint': omni_sls.get("endpoint", common_sls.get("endpoint", "cn-hangzhou.log.aliyuncs.com")),
                'project': omni_sls.get("project", common_sls.get("project")),
                'logstore': omni_sls.get("logstore", "omni-agent"),
                'access_key_id': omni_sls.get("access-key-id", common_sls.get("access-key-id")),
                'access_key_secret': omni_sls.get("access-key-secret", common_sls.get("access-key-secret")),
                'batch_size': 100,
                'flush_interval_ms': 3000,
            }
    else:
        # 从环境变量读取配置
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_format = os.getenv('LOG_FORMAT', 'text')
        
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
    
    return log_level, log_format, sls_config


# 初始化基础日志（用于启动阶段）
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_format = os.getenv('LOG_FORMAT', 'text')
setup_logging(level=log_level, format=log_format)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Omni-Agent starting...")
    
    # 获取 Nacos 连接信息（这些必须从环境变量获取，因为 Nacos 还未初始化）
    nacos_config_enabled = os.getenv('NACOS_CONFIG_ENABLED', 'true').lower() == 'true'
    nacos_server = os.getenv('NACOS_SERVER_ADDR', '47.114.90.156:8848')
    nacos_namespace = os.getenv('NACOS_NAMESPACE', 'public')
    nacos_username = os.getenv('NACOS_USERNAME', 'nacos')
    nacos_password = os.getenv('NACOS_PASSWORD', 'nacos')
    nacos_group = os.getenv('NACOS_GROUP', 'DEEPKNOW_GROUP')
    
    # 初始化 Nacos 配置中心
    if nacos_config_enabled:
        logger.info("Initializing Nacos Config...", server=nacos_server, group=nacos_group)
        try:
            init_nacos_config(
                server_addr=nacos_server,
                namespace=nacos_namespace,
                username=nacos_username,
                password=nacos_password,
                group=nacos_group
            )
            
            # 预加载配置
            nacos_config = get_nacos_config()
            nacos_config.get_config("common.yaml")
            nacos_config.get_config("omni-agent.yaml")
            
            logger.info("Nacos Config initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Nacos Config, falling back to env vars", error=str(e))
    
    # 重新初始化日志（可能从 Nacos 读取了新配置）
    log_level, log_format, sls_config = _init_config_from_nacos_or_env()
    setup_logging(level=log_level, format=log_format, sls_config=sls_config)
    logger.info("Logging reconfigured", level=log_level, format=log_format, sls_enabled=sls_config is not None)
    
    # 启动会话管理器
    session_manager = get_session_manager()
    await session_manager.start()
    
    # 获取 gRPC 配置
    if get_nacos_config():
        grpc_port = int(_get_config("service.grpc-port", 50051))
        grpc_enabled = _get_config("service.grpc-enabled", True)
    else:
        grpc_port = int(os.getenv('GRPC_PORT', '50051'))
        grpc_enabled = os.getenv('GRPC_ENABLED', 'true').lower() == 'true'
    
    # 启动 gRPC 服务器（如果启用）
    grpc_server = None
    if grpc_enabled:
        from .server.grpc import GrpcServer
        grpc_server = GrpcServer(port=grpc_port)
        await grpc_server.start()
    
    # 注册到 Nacos（如果启用）
    nacos_registry = None
    if get_nacos_config():
        nacos_registry_enabled = _get_config("nacos.enabled", False)
        nacos_service_name = _get_config("nacos.service-name", "omni-agent")
    else:
        nacos_registry_enabled = os.getenv('NACOS_ENABLED', 'false').lower() == 'true'
        nacos_service_name = os.getenv('NACOS_SERVICE_NAME', 'omni-agent')
    
    if nacos_registry_enabled:
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
    nacos_config = get_nacos_config()
    return {
        "status": "healthy",
        "version": "0.1.0",
        "sessions_count": session_manager.count(),
        "nacos_config_enabled": nacos_config is not None
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


# 提供配置获取函数供其他模块使用
def get_app_config(key_path: str, default=None):
    """获取应用配置（供其他模块调用）"""
    return _get_config(key_path, default)


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
