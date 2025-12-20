"""
Nacos 配置中心模块

从 Nacos 配置中心读取配置，替代环境变量
"""

import os
import yaml
from typing import Any, Dict, Optional, Callable
import nacos
from .logging import get_logger

logger = get_logger(__name__)


class NacosConfig:
    """Nacos 配置中心客户端"""
    
    def __init__(
        self,
        server_addr: str,
        namespace: str = "public",
        username: Optional[str] = None,
        password: Optional[str] = None,
        group: str = "DEFAULT_GROUP"
    ):
        self.server_addr = server_addr
        self.namespace = namespace
        self.group = group
        
        # 初始化 Nacos 客户端
        self.client = nacos.NacosClient(
            server_addr,
            namespace=namespace,
            username=username,
            password=password
        )
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        # 回调函数
        self._callbacks: Dict[str, list] = {}
        
        logger.info(
            "NacosConfig initialized",
            server_addr=server_addr,
            namespace=namespace,
            group=group
        )
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """解析 YAML 配置"""
        try:
            return yaml.safe_load(content) or {}
        except Exception as e:
            logger.error("Failed to parse YAML config", error=str(e))
            return {}
    
    def get_config(self, data_id: str, group: Optional[str] = None) -> Dict[str, Any]:
        """获取配置"""
        group = group or self.group
        cache_key = f"{group}/{data_id}"
        
        # 检查缓存
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        try:
            content = self.client.get_config(data_id, group)
            if content:
                config = self._parse_yaml(content)
                self._config_cache[cache_key] = config
                logger.info(
                    "Config loaded from Nacos",
                    data_id=data_id,
                    group=group
                )
                return config
        except Exception as e:
            logger.error(
                "Failed to get config from Nacos",
                data_id=data_id,
                group=group,
                error=str(e)
            )
        
        return {}
    
    def get_value(self, data_id: str, key_path: str, default: Any = None, group: Optional[str] = None) -> Any:
        """获取配置中的特定值
        
        Args:
            data_id: 配置 ID
            key_path: 键路径，用 . 分隔，如 "database.host"
            default: 默认值
            group: 配置组
        
        Returns:
            配置值或默认值
        """
        config = self.get_config(data_id, group)
        
        keys = key_path.split('.')
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def add_listener(self, data_id: str, callback: Callable[[Dict[str, Any]], None], group: Optional[str] = None):
        """添加配置变更监听器"""
        group = group or self.group
        cache_key = f"{group}/{data_id}"
        
        if cache_key not in self._callbacks:
            self._callbacks[cache_key] = []
            
            # 注册 Nacos 监听
            def on_config_change(args):
                content = args.get('raw_content', '')
                new_config = self._parse_yaml(content)
                self._config_cache[cache_key] = new_config
                
                logger.info(
                    "Config changed",
                    data_id=data_id,
                    group=group
                )
                
                # 触发所有回调
                for cb in self._callbacks.get(cache_key, []):
                    try:
                        cb(new_config)
                    except Exception as e:
                        logger.error(
                            "Config change callback error",
                            error=str(e)
                        )
            
            self.client.add_config_watcher(data_id, group, on_config_change)
        
        self._callbacks[cache_key].append(callback)
        logger.info(
            "Config listener added",
            data_id=data_id,
            group=group
        )
    
    def refresh_all(self):
        """刷新所有配置缓存"""
        for cache_key in list(self._config_cache.keys()):
            group, data_id = cache_key.split('/', 1)
            try:
                content = self.client.get_config(data_id, group)
                if content:
                    self._config_cache[cache_key] = self._parse_yaml(content)
            except Exception as e:
                logger.error(
                    "Failed to refresh config",
                    data_id=data_id,
                    group=group,
                    error=str(e)
                )


# 全局配置实例
_nacos_config: Optional[NacosConfig] = None


def init_nacos_config(
    server_addr: str,
    namespace: str = "public",
    username: Optional[str] = None,
    password: Optional[str] = None,
    group: str = "DEFAULT_GROUP"
) -> NacosConfig:
    """初始化 Nacos 配置中心客户端"""
    global _nacos_config
    _nacos_config = NacosConfig(
        server_addr=server_addr,
        namespace=namespace,
        username=username,
        password=password,
        group=group
    )
    return _nacos_config


def get_nacos_config() -> Optional[NacosConfig]:
    """获取 Nacos 配置中心客户端实例"""
    return _nacos_config


def get_config_value(data_id: str, key_path: str, default: Any = None, group: Optional[str] = None) -> Any:
    """快捷获取配置值"""
    if _nacos_config:
        return _nacos_config.get_value(data_id, key_path, default, group)
    return default
