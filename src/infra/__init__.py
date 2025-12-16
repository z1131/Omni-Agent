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
]
