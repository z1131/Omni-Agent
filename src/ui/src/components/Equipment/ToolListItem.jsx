import React from 'react';
import clsx from 'clsx';
import { Check, Settings, Trash2, ChevronDown, ChevronRight, Power, Plug } from 'lucide-react';

const ToolListItem = ({ tool, isExpanded, onToggle, onInstall, onUninstall }) => {
    const { id, name, description, icon: Icon, installed, category, type } = tool;
    const isMcp = type === 'mcp';

    return (
        <div className="border-b border-white/5 last:border-b-0">
            {/* Summary View - 收起状态 */}
            <div
                onClick={onToggle}
                className={clsx(
                    'flex items-center justify-between px-3 py-3 cursor-pointer transition-all duration-200',
                    'hover:bg-white/5',
                    isExpanded && 'bg-white/5'
                )}
            >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                    {/* 图标 */}
                    <div className={clsx(
                        'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                        installed ? 'bg-secondary/20 text-secondary' : 'bg-white/5 text-gray-400',
                        isMcp && 'ring-1 ring-purple-500/30'
                    )}>
                        <Icon size={16} />
                    </div>
                    
                    {/* 名称 */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                            <h4 className="text-sm font-semibold text-white truncate">{name}</h4>
                            {isMcp && (
                                <span className="bg-purple-500/20 text-purple-400 text-[8px] font-bold px-1.5 py-0.5 rounded">
                                    MCP
                                </span>
                            )}
                        </div>
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider">{category}</p>
                    </div>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                    {/* 状态标签 */}
                    {installed && (
                        <span className="bg-secondary/20 text-secondary text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center">
                            <Check size={10} className="mr-1" />
                            已启用
                        </span>
                    )}
                    
                    {/* 展开/收起箭头 */}
                    <div className="text-gray-400 transition-transform duration-200">
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    </div>
                </div>
            </div>

            {/* Detail View - 展开状态 */}
            <div
                className={clsx(
                    'overflow-hidden transition-all duration-300 ease-in-out',
                    isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
                )}
            >
                <div className="px-3 pb-3 pt-1">
                    {/* 描述 */}
                    <p className="text-xs text-gray-400 leading-relaxed mb-3 pl-11">
                        {description}
                    </p>
                    
                    {/* MCP 配置信息提示 */}
                    {isMcp && (
                        <div className="text-[10px] text-purple-400/70 mb-2 pl-11 flex items-center">
                            <Plug size={10} className="mr-1" />
                            通过 MCP 协议连接外部服务
                        </div>
                    )}
                    
                    {/* 操作按钮 */}
                    <div className="flex space-x-2 pl-11">
                        {installed ? (
                            <>
                                <button className="flex-1 bg-white/5 hover:bg-white/10 text-white py-1.5 px-3 rounded-lg text-xs font-medium transition-colors flex items-center justify-center">
                                    <Settings size={12} className="mr-1.5" />
                                    配置
                                </button>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onUninstall(id);
                                    }}
                                    className="bg-red-500/10 hover:bg-red-500/20 text-red-500 py-1.5 px-3 rounded-lg text-xs font-medium transition-colors flex items-center justify-center"
                                >
                                    <Power size={12} className="mr-1.5" />
                                    禁用
                                </button>
                            </>
                        ) : (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onInstall(id);
                                }}
                                className={clsx(
                                    "flex-1 py-1.5 px-3 rounded-lg text-xs font-medium transition-all duration-200 flex items-center justify-center",
                                    isMcp 
                                        ? "bg-purple-500/20 hover:bg-purple-500 text-purple-400 hover:text-white"
                                        : "bg-primary/20 hover:bg-primary text-primary hover:text-white"
                                )}
                            >
                                <Power size={12} className="mr-1.5" />
                                启用
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ToolListItem;
