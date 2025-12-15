import React, { useState, useEffect } from 'react';
import { Search, Globe, Code, FileText, Image, Database, Terminal, ChevronDown, ChevronRight, Package, Plug } from 'lucide-react';
import clsx from 'clsx';
import ToolListItem from './ToolListItem';

const initialTools = [];

const EquipmentPanel = ({ compact = false }) => {
    const [tools, setTools] = useState(initialTools);
    const [mcpServers, setMcpServers] = useState([]);
    const [search, setSearch] = useState('');
    const [filter, setFilter] = useState('全部');
    const [activeToolId, setActiveToolId] = useState(null);
    const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);

    // 加载内置工具
    useEffect(() => {
        fetch('http://localhost:8000/tools')
            .then(res => res.json())
            .then(data => {
                const iconMap = {
                    'Research': Globe,
                    'Development': Terminal,
                    'Creative': Image,
                    'Utility': FileText,
                    'Data': Database,
                    'File Operations': FileText,
                    'General': Code,
                    '开发工具': Terminal,
                    '文件操作': FileText,
                    'MCP 工具': Plug
                };

                // 过滤掉 MCP 工具（它们由单独接口返回）
                const builtinTools = data.tools.filter(t => !t.is_mcp).map(t => ({
                    ...t,
                    installed: t.enabled !== undefined ? t.enabled : t.installed,
                    icon: iconMap[t.category] || Code,
                    type: 'builtin'
                }));
                setTools(builtinTools);
            })
            .catch(err => console.error("Failed to load tools", err));
    }, []);

    // 加载 MCP 服务器
    useEffect(() => {
        fetch('http://localhost:8000/mcp/servers')
            .then(res => res.json())
            .then(data => {
                const servers = data.servers.map(s => ({
                    ...s,
                    installed: s.enabled,
                    icon: Plug,
                    category: 'MCP 工具',
                    type: 'mcp'
                }));
                setMcpServers(servers);
            })
            .catch(err => console.error("Failed to load MCP servers", err));
    }, []);

    const handleInstall = (id, type = 'builtin') => {
        if (type === 'mcp') {
            // MCP 工具启用
            setMcpServers(mcpServers.map(s => s.id === id ? { ...s, installed: true } : s));
            
            fetch(`http://localhost:8000/mcp/servers/${id}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: true })
            }).catch(err => {
                console.error("Enable MCP server failed", err);
                setMcpServers(mcpServers.map(s => s.id === id ? { ...s, installed: false } : s));
            });
        } else {
            // 内置工具启用
            setTools(tools.map(t => t.id === id ? { ...t, installed: true } : t));

            fetch('http://localhost:8000/tools/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool_id: id, install: true })
            }).catch(err => {
                console.error("Install failed", err);
                setTools(tools.map(t => t.id === id ? { ...t, installed: false } : t));
            });
        }
    };

    const handleUninstall = (id, type = 'builtin') => {
        if (type === 'mcp') {
            // MCP 工具禁用
            setMcpServers(mcpServers.map(s => s.id === id ? { ...s, installed: false } : s));
            
            fetch(`http://localhost:8000/mcp/servers/${id}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: false })
            }).catch(err => {
                console.error("Disable MCP server failed", err);
                setMcpServers(mcpServers.map(s => s.id === id ? { ...s, installed: true } : s));
            });
        } else {
            // 内置工具禁用
            setTools(tools.map(t => t.id === id ? { ...t, installed: false } : t));

            fetch('http://localhost:8000/tools/install', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool_id: id, install: false })
            }).catch(err => {
                console.error("Uninstall failed", err);
                setTools(tools.map(t => t.id === id ? { ...t, installed: true } : t));
            });
        }
    };

    const handleToggleTool = (id) => {
        // 互斥展开：如果点击已展开的工具，则收起；否则展开新工具并收起其他
        setActiveToolId(activeToolId === id ? null : id);
    };

    // 合并内置工具和 MCP 工具
    const allTools = [...tools, ...mcpServers];

    const filteredTools = allTools.filter(t =>
        (filter === '全部' || t.category === filter) &&
        (t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()))
    );

    const categories = ['全部', ...new Set(allTools.map(t => t.category))];
    const enabledCount = allTools.filter(t => t.installed).length;

    return (
        <div className="flex flex-col h-full">
            {/* 面板头部 - 可折叠 */}
            {compact && (
                <div 
                    onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
                    className="flex items-center justify-between px-2 py-2 cursor-pointer hover:bg-white/5 rounded-lg mb-1 transition-colors"
                >
                    <div className="flex items-center space-x-2">
                        <Package size={14} className="text-gray-400" />
                        <span className="text-xs font-medium text-gray-300">
                            工具 ({enabledCount}/{allTools.length})
                        </span>
                    </div>
                    <div className="text-gray-400 transition-transform duration-200">
                        {isPanelCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                    </div>
                </div>
            )}

            {/* 面板内容 */}
            <div className={clsx(
                'flex flex-col flex-1 min-h-0 transition-all duration-300 ease-in-out overflow-hidden',
                compact && isPanelCollapsed ? 'max-h-0 opacity-0' : 'max-h-full opacity-100'
            )}>
                {/* 搜索栏 - 仅非 compact 模式 */}
                {!compact && (
                    <div className="flex flex-col md:flex-row justify-between items-center mb-4 space-y-2 md:space-y-0">
                        <div className="relative w-full md:w-64">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={14} />
                            <input
                                type="text"
                                placeholder="搜索工具..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full bg-surface border border-white/10 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-primary/50 transition-all"
                            />
                        </div>

                        <div className="flex space-x-1 overflow-x-auto w-full md:w-auto">
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setFilter(cat)}
                                    className={clsx(
                                        'px-3 py-1.5 rounded-lg text-[10px] font-medium whitespace-nowrap transition-colors',
                                        filter === cat
                                            ? 'bg-primary text-white'
                                            : 'bg-surface text-gray-400 hover:text-white hover:bg-white/10'
                                    )}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Compact 模式下的迷你搜索栏 */}
                {compact && !isPanelCollapsed && (
                    <div className="relative mb-2">
                        <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-500" size={12} />
                        <input
                            type="text"
                            placeholder="搜索..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-[11px] text-white focus:outline-none focus:border-primary/50 transition-all"
                        />
                    </div>
                )}

                {/* 工具列表 */}
                <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent rounded-lg bg-white/[0.02] border border-white/5">
                    {filteredTools.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-gray-500 text-xs py-8">
                            暂无工具
                        </div>
                    ) : (
                        filteredTools.map(tool => (
                            <ToolListItem
                                key={tool.id}
                                tool={tool}
                                isExpanded={activeToolId === tool.id}
                                onToggle={() => handleToggleTool(tool.id)}
                                onInstall={(id) => handleInstall(id, tool.type)}
                                onUninstall={(id) => handleUninstall(id, tool.type)}
                            />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default EquipmentPanel;
