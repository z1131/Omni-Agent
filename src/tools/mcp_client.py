"""
MCP Client - MCP 协议客户端

负责：
1. 管理 MCP Server 配置
2. 将 MCP 工具转换为 Qwen-Agent 兼容格式
3. 验证 MCP Server 连接
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import subprocess
import shutil


@dataclass
class MCPServerConfig:
    """MCP Server 配置"""
    id: str                          # 唯一标识
    name: str                        # 显示名称
    description: str                 # 描述
    command: str                     # 启动命令 (如 uvx, npx, python)
    args: List[str] = field(default_factory=list)  # 命令参数
    env: Dict[str, str] = field(default_factory=dict)  # 环境变量
    enabled: bool = False            # 是否启用
    
    def to_qwen_format(self) -> Dict[str, Any]:
        """
        转换为 Qwen-Agent mcpServers 格式
        
        Qwen-Agent 接受的格式:
        {
            "mcpServers": {
                "server_name": {
                    "command": "uvx",
                    "args": ["mcp-server-xxx", ...],
                    "env": {"KEY": "value"}
                }
            }
        }
        """
        config = {
            "command": self.command,
            "args": self.args
        }
        if self.env:
            config["env"] = self.env
        
        return {
            "mcpServers": {
                self.id: config
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于存储和 API）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            enabled=data.get("enabled", False)
        )


class MCPClient:
    """
    MCP 客户端管理器
    
    负责管理多个 MCP Server 的配置和连接
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "mcp_servers.json"
        self._servers: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """加载 MCP Server 配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for server_data in data.get("servers", []):
                        server = MCPServerConfig.from_dict(server_data)
                        self._servers[server.id] = server
            except Exception as e:
                print(f"Warning: Failed to load MCP config: {e}")
    
    def _save_config(self):
        """保存 MCP Server 配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "servers": [server.to_dict() for server in self._servers.values()]
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save MCP config: {e}")
    
    def register_server(self, config: MCPServerConfig) -> str:
        """注册 MCP Server"""
        self._servers[config.id] = config
        self._save_config()
        return config.id
    
    def unregister_server(self, server_id: str) -> bool:
        """注销 MCP Server"""
        if server_id in self._servers:
            del self._servers[server_id]
            self._save_config()
            return True
        return False
    
    def enable_server(self, server_id: str) -> bool:
        """启用 MCP Server"""
        if server_id in self._servers:
            self._servers[server_id].enabled = True
            self._save_config()
            return True
        return False
    
    def disable_server(self, server_id: str) -> bool:
        """禁用 MCP Server"""
        if server_id in self._servers:
            self._servers[server_id].enabled = False
            self._save_config()
            return True
        return False
    
    def toggle_server(self, server_id: str) -> Optional[bool]:
        """切换 MCP Server 状态"""
        if server_id in self._servers:
            new_state = not self._servers[server_id].enabled
            self._servers[server_id].enabled = new_state
            self._save_config()
            return new_state
        return None
    
    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """获取 MCP Server 配置"""
        return self._servers.get(server_id)
    
    def get_all_servers(self) -> List[MCPServerConfig]:
        """获取所有 MCP Server"""
        return list(self._servers.values())
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """获取所有启用的 MCP Server"""
        return [s for s in self._servers.values() if s.enabled]
    
    def get_enabled_tools_for_agent(self) -> List[Dict[str, Any]]:
        """
        获取所有启用的 MCP Server，转换为 Qwen-Agent 格式
        
        Returns:
            Qwen-Agent function_list 中可用的 MCP 工具配置列表
        """
        return [server.to_qwen_format() for server in self.get_enabled_servers()]
    
    def check_command_available(self, command: str) -> bool:
        """检查命令是否可用"""
        return shutil.which(command) is not None
    
    def validate_server(self, server_id: str) -> Dict[str, Any]:
        """
        验证 MCP Server 配置
        
        Returns:
            {"valid": bool, "message": str}
        """
        server = self._servers.get(server_id)
        if not server:
            return {"valid": False, "message": "Server not found"}
        
        # 检查命令是否存在
        if not self.check_command_available(server.command):
            return {
                "valid": False, 
                "message": f"命令 '{server.command}' 不可用，请先安装"
            }
        
        return {"valid": True, "message": "配置有效"}


# 全局单例
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取全局 MCP 客户端实例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# 预定义的常用 MCP Server 模板
MCP_SERVER_TEMPLATES = {
    "sqlite": MCPServerConfig(
        id="mcp_sqlite",
        name="SQLite 数据库",
        description="查询和操作 SQLite 数据库，支持 SQL 查询、表管理等",
        command="uvx",
        args=["mcp-server-sqlite", "--db-path", "database.db"],
        enabled=False
    ),
    "filesystem": MCPServerConfig(
        id="mcp_filesystem",
        name="文件系统",
        description="访问和操作本地文件系统，支持读写文件、目录浏览等",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
        enabled=False
    ),
    "github": MCPServerConfig(
        id="mcp_github",
        name="GitHub",
        description="与 GitHub 交互，支持仓库管理、Issue、PR 等操作",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        enabled=False
    ),
    "brave_search": MCPServerConfig(
        id="mcp_brave_search",
        name="Brave 搜索",
        description="使用 Brave Search API 进行网络搜索",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": ""},
        enabled=False
    ),
    "memory": MCPServerConfig(
        id="mcp_memory",
        name="知识图谱记忆",
        description="基于知识图谱的持久化记忆系统",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        enabled=False
    ),
    "puppeteer": MCPServerConfig(
        id="mcp_puppeteer",
        name="网页自动化",
        description="使用 Puppeteer 进行网页自动化操作，支持截图、表单填写等",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        enabled=False
    ),
    "fetch": MCPServerConfig(
        id="mcp_fetch",
        name="网页抓取",
        description="抓取网页内容并转换为 Markdown 格式",
        command="uvx",
        args=["mcp-server-fetch"],
        enabled=False
    ),
}
