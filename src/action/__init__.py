"""
Omni-Agent 执行层

提供工具调用、MCP 客户端等执行能力
"""

from .manager import ToolManager, ToolInfo, get_tool_manager, init_tool_manager
from .mcp_client import MCPClient

__all__ = [
    'ToolManager',
    'ToolInfo',
    'get_tool_manager',
    'init_tool_manager',
    'MCPClient',
]
