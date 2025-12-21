"""
Nacos 服务注册模块

将 Omni-Agent 注册到 Nacos 服务中心
"""

import os
import socket
import nacos
from typing import Optional
from .logging import get_logger

logger = get_logger(__name__)


class NacosRegistry:
    """Nacos 服务注册器"""
    
    def __init__(
        self,
        server_addr: str,
        namespace: str = "public",
        username: Optional[str] = None,
        password: Optional[str] = None,
        service_name: str = "omni-agent",
        service_port: int = 50051,
        group_name: str = "DEFAULT_GROUP",
        cluster_name: str = "DEFAULT",
        weight: float = 1.0,
        metadata: Optional[dict] = None
    ):
        self.server_addr = server_addr
        self.namespace = namespace
        self.service_name = service_name
        self.service_port = service_port
        self.group_name = group_name
        self.cluster_name = cluster_name
        self.weight = weight
        self.metadata = metadata or {}
        
        # 获取本机 IP
        self.service_ip = self._get_local_ip()
        
        # 初始化 Nacos 客户端
        self.client = nacos.NacosClient(
            server_addr,
            namespace=namespace,
            username=username,
            password=password
        )
        
        self._registered = False
        
        logger.info(
            "NacosRegistry initialized",
            server_addr=server_addr,
            service_name=service_name,
            service_ip=self.service_ip,
            service_port=service_port
        )
    
    def _get_local_ip(self) -> str:
        """获取本机 IP 地址"""
        # 优先使用环境变量指定的 IP
        ip = os.getenv('SERVICE_IP')
        if ip:
            return ip
        
        # 尝试获取本机 IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def register(self) -> bool:
        """注册服务到 Nacos"""
        try:
            # 使用 SDK 原生心跳功能：heartbeat_interval 参数会自动启动后台心跳线程
            self.client.add_naming_instance(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=self.cluster_name,
                weight=self.weight,
                metadata=self.metadata,
                enable=True,
                healthy=True,
                ephemeral=True,  # 临时实例，需要心跳保持存活
                heartbeat_interval=5,  # 每 5 秒自动发送心跳
                group_name=self.group_name
            )
            self._registered = True
            logger.info(
                "Service registered to Nacos with auto heartbeat",
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port
            )
            return True
        except Exception as e:
            logger.error("Failed to register service to Nacos", error=str(e))
            return False
    
    def deregister(self) -> bool:
        """从 Nacos 注销服务"""
        if not self._registered:
            return True
        
        try:
            self.client.remove_naming_instance(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=self.cluster_name,
                group_name=self.group_name
            )
            self._registered = False
            logger.info(
                "Service deregistered from Nacos",
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port
            )
            return True
        except Exception as e:
            logger.error("Failed to deregister service from Nacos", error=str(e))
            return False
    
    def send_heartbeat(self) -> bool:
        """发送心跳"""
        try:
            self.client.send_heartbeat(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=self.cluster_name,
                weight=self.weight,
                metadata=self.metadata,
                group_name=self.group_name
            )
            return True
        except Exception as e:
            logger.warning("Failed to send heartbeat", error=str(e))
            return False


# 全局注册器实例
_registry: Optional[NacosRegistry] = None


def init_nacos_registry(
    server_addr: str,
    namespace: str = "public",
    username: Optional[str] = None,
    password: Optional[str] = None,
    service_name: str = "omni-agent",
    service_port: int = 50051,
    group_name: str = "DEFAULT_GROUP",
    metadata: Optional[dict] = None
) -> NacosRegistry:
    """初始化 Nacos 注册器"""
    global _registry
    _registry = NacosRegistry(
        server_addr=server_addr,
        namespace=namespace,
        username=username,
        password=password,
        service_name=service_name,
        service_port=service_port,
        group_name=group_name,
        metadata=metadata
    )
    return _registry


def get_nacos_registry() -> Optional[NacosRegistry]:
    """获取 Nacos 注册器实例"""
    return _registry
