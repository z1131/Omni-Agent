"""
Omni-Agent 基础设施层

提供日志、埋点、钩子、配置等基础能力
"""

from .logging import (
    get_logger,
    setup_logging,
    log_context,
    logged,
    generate_trace_id,
    Logger,
    LogSpan,
)

from .metrics import (
    get_metrics,
    setup_metrics,
    tracked,
    EventStatus,
    MetricsService,
)

from .hooks import (
    AgentHooks,
    CompositeHooks,
    LoggingHooks,
)

from .nacos import (
    NacosRegistry,
    init_nacos_registry,
    get_nacos_registry,
)

from .nacos_config import (
    NacosConfig,
    init_nacos_config,
    get_nacos_config,
    get_config_value,
)

__all__ = [
    # Logging
    'get_logger',
    'setup_logging', 
    'log_context',
    'logged',
    'generate_trace_id',
    'Logger',
    'LogSpan',
    # Metrics
    'get_metrics',
    'setup_metrics',
    'tracked',
    'EventStatus',
    'MetricsService',
    # Hooks
    'AgentHooks',
    'CompositeHooks',
    'LoggingHooks',
    # Nacos Registry
    'NacosRegistry',
    'init_nacos_registry',
    'get_nacos_registry',
    # Nacos Config
    'NacosConfig',
    'init_nacos_config',
    'get_nacos_config',
    'get_config_value',
]

