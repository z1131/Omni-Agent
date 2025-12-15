"""
Tool Manager - 工具管理器

负责管理 Agent 可用的工具：
1. 注册/发现工具
2. 启用/禁用工具
3. 持久化配置
4. 提供工具列表给 Agent
5. 集成 MCP 工具
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from qwen_agent.tools.base import BaseTool
from src.tools.mcp_client import get_mcp_client, MCPServerConfig, MCP_SERVER_TEMPLATES

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
TOOLS_CONFIG_FILE = CONFIG_DIR / "tools.json"


class ToolInfo:
    """工具信息类"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: str = "General",
        enabled: bool = True,
        tool_class: Optional[type] = None,
        is_builtin: bool = True
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.enabled = enabled
        self.tool_class = tool_class  # BaseTool 子类
        self.is_builtin = is_builtin  # True=内置, False=MCP
    
    def to_dict(self) -> dict:
        """转换为字典（用于 API 返回和配置存储）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
            "is_builtin": self.is_builtin
        }
    
    @classmethod
    def from_dict(cls, data: dict, tool_class: Optional[type] = None) -> "ToolInfo":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data.get("category", "General"),
            enabled=data.get("enabled", True),
            tool_class=tool_class,
            is_builtin=data.get("is_builtin", True)
        )


class ToolManager:
    """
    工具管理器
    
    使用示例:
        manager = ToolManager()
        manager.register_builtin_tool(CodeInterpreter, category="Development")
        manager.enable_tool("code_interpreter")
        
        enabled_tools = manager.get_enabled_tools()
        agent = OmniAgent(function_list=enabled_tools)
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or TOOLS_CONFIG_FILE
        self._tools: Dict[str, ToolInfo] = {}
        self._load_config()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """从配置文件加载工具状态"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 只加载状态，不加载工具定义（工具定义由代码注册）
                    self._saved_states = {
                        tool_id: tool_data.get("enabled", True)
                        for tool_id, tool_data in config.get("tools", {}).items()
                    }
            except Exception as e:
                print(f"Warning: Failed to load tools config: {e}")
                self._saved_states = {}
        else:
            self._saved_states = {}
    
    def _save_config(self):
        """保存工具状态到配置文件"""
        self._ensure_config_dir()
        config = {
            "tools": {
                tool_id: tool_info.to_dict()
                for tool_id, tool_info in self._tools.items()
            }
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save tools config: {e}")
    
    def register_builtin_tool(
        self,
        tool_class: type,
        category: str = "General",
        enabled: bool = True
    ) -> str:
        """
        注册内置工具（Python 类）
        
        Args:
            tool_class: BaseTool 的子类
            category: 工具分类
            enabled: 默认是否启用
        
        Returns:
            工具 ID
        """
        # 从 tool_class 获取元信息
        tool_id = getattr(tool_class, 'name', tool_class.__name__.lower())
        
        # name_for_human 可能是 property，需要实例化或用 fallback
        tool_name_attr = getattr(tool_class, 'name_for_human', None)
        if isinstance(tool_name_attr, property):
            # 如果是 property，使用 tool_id 作为名称
            tool_name = tool_id
        else:
            tool_name = tool_name_attr or tool_id
        
        tool_desc = getattr(tool_class, 'description', f'{tool_id} tool')
        if isinstance(tool_desc, property):
            tool_desc = f'{tool_id} tool'
        
        # 如果配置文件中有保存的状态，使用保存的状态
        if tool_id in self._saved_states:
            enabled = self._saved_states[tool_id]
        
        tool_info = ToolInfo(
            id=tool_id,
            name=tool_name,
            description=tool_desc,
            category=category,
            enabled=enabled,
            tool_class=tool_class,
            is_builtin=True
        )
        
        self._tools[tool_id] = tool_info
        return tool_id
    
    def register_mcp_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        mcp_server_config: dict,
        category: str = "MCP",
        enabled: bool = False  # MCP 工具默认禁用
    ) -> str:
        """
        注册 MCP 工具（外部服务）
        
        Args:
            tool_id: 工具唯一标识
            name: 工具显示名称
            description: 工具描述
            mcp_server_config: MCP 服务器配置
            category: 工具分类
            enabled: 默认是否启用
        
        Returns:
            工具 ID
        """
        # 如果配置文件中有保存的状态，使用保存的状态
        if tool_id in self._saved_states:
            enabled = self._saved_states[tool_id]
        
        tool_info = ToolInfo(
            id=tool_id,
            name=name,
            description=description,
            category=category,
            enabled=enabled,
            tool_class=None,  # MCP 工具没有本地类
            is_builtin=False
        )
        # 存储 MCP 配置
        tool_info.mcp_config = mcp_server_config
        
        self._tools[tool_id] = tool_info
        return tool_id
    
    def enable_tool(self, tool_id: str) -> bool:
        """启用工具"""
        if tool_id in self._tools:
            self._tools[tool_id].enabled = True
            self._save_config()
            return True
        return False
    
    def disable_tool(self, tool_id: str) -> bool:
        """禁用工具"""
        if tool_id in self._tools:
            self._tools[tool_id].enabled = False
            self._save_config()
            return True
        return False
    
    def toggle_tool(self, tool_id: str) -> Optional[bool]:
        """切换工具状态，返回新状态"""
        if tool_id in self._tools:
            new_state = not self._tools[tool_id].enabled
            self._tools[tool_id].enabled = new_state
            self._save_config()
            return new_state
        return None
    
    def get_tool(self, tool_id: str) -> Optional[ToolInfo]:
        """获取工具信息"""
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> List[ToolInfo]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_enabled_tools(self) -> List[Union[BaseTool, str, Dict[str, Any]]]:
        """
        获取所有启用的工具，返回 Qwen-Agent 可用的格式
        
        Returns:
            工具列表，内置工具返回类名字符串，MCP 工具返回配置字典
        """
        enabled_tools = []
        
        # 内置工具
        for tool_info in self._tools.values():
            if tool_info.enabled:
                if tool_info.is_builtin and tool_info.tool_class:
                    # 内置工具：返回工具名称字符串（Qwen-Agent 会自动实例化）
                    enabled_tools.append(tool_info.id)
        
        # MCP 工具
        mcp_client = get_mcp_client()
        enabled_tools.extend(mcp_client.get_enabled_tools_for_agent())
        
        return enabled_tools
    
    def get_enabled_tool_instances(self) -> List[BaseTool]:
        """
        获取所有启用的工具实例
        
        Returns:
            BaseTool 实例列表
        """
        instances = []
        for tool_info in self._tools.values():
            if tool_info.enabled and tool_info.is_builtin and tool_info.tool_class:
                try:
                    instance = tool_info.tool_class()
                    instances.append(instance)
                except Exception as e:
                    print(f"Warning: Failed to instantiate tool {tool_info.id}: {e}")
        return instances
    
    def to_api_response(self) -> List[dict]:
        """转换为 API 响应格式（包含内置工具和 MCP 工具）"""
        result = [tool.to_dict() for tool in self._tools.values()]
        
        # 添加 MCP 工具
        mcp_client = get_mcp_client()
        for server in mcp_client.get_all_servers():
            result.append({
                "id": server.id,
                "name": server.name,
                "description": server.description,
                "category": "MCP 工具",
                "enabled": server.enabled,
                "is_builtin": False,
                "is_mcp": True,
                "mcp_config": {
                    "command": server.command,
                    "args": server.args,
                    "env": {k: "***" if v else "" for k, v in server.env.items()}  # 隐藏敏感信息
                }
            })
        
        return result


# 全局单例
_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """获取全局工具管理器实例"""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager


def init_tool_manager() -> ToolManager:
    """
    初始化工具管理器并注册默认工具
    
    在应用启动时调用此函数
    """
    manager = get_tool_manager()
    
    # 注册 Qwen-Agent 内置工具
    try:
        from qwen_agent.tools.code_interpreter import CodeInterpreter
        manager.register_builtin_tool(
            CodeInterpreter,
            category="Development",
            enabled=True
        )
    except ImportError:
        print("Warning: CodeInterpreter not available")
    
    # 注册自定义内置工具
    try:
        from src.tools.builtins.file_reader import FileReader
        manager.register_builtin_tool(
            FileReader,
            category="File Operations",
            enabled=True
        )
    except ImportError:
        pass  # 工具还未创建
    
    try:
        from src.tools.builtins.web_search import WebSearch
        manager.register_builtin_tool(
            WebSearch,
            category="Research",
            enabled=False  # 默认禁用，需要配置 API
        )
    except ImportError:
        pass  # 工具还未创建
    
    return manager
