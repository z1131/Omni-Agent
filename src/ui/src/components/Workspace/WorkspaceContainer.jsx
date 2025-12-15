import React, { useState } from 'react';
import { Code, FileText, BarChart2, Layers } from 'lucide-react';
import CodeEditor from './CodeEditor';

const WorkspaceContainer = ({ compact = false }) => {
    const [activeTab, setActiveTab] = useState('code');

    const tabs = [
        { id: 'code', label: '代码', icon: Code },
        { id: 'docs', label: '文档', icon: FileText },
        { id: 'data', label: '数据', icon: BarChart2 },
    ];

    return (
        <div className="flex flex-col h-full">
            {/* Tabs */}
            <div className="flex items-center space-x-1 mb-4 border-b border-white/10 pb-1">
                {tabs.map(tab => {
                    const Icon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center px-4 py-2 rounded-t-lg text-sm font-medium transition-all ${activeTab === tab.id
                                ? 'bg-white/10 text-white border-b-2 border-primary'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            <Icon size={14} className="mr-2" />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Content Area */}
            <div className="flex-1 relative">
                {activeTab === 'code' && <CodeEditor />}

                {activeTab === 'docs' && (
                    <div className="h-full flex items-center justify-center bg-white/5 rounded-xl border border-white/10">
                        <div className="text-center text-gray-400">
                            <FileText size={48} className="mx-auto mb-4 opacity-50" />
                            <p>文档预览（开发中）</p>
                        </div>
                    </div>
                )}

                {activeTab === 'data' && (
                    <div className="h-full flex items-center justify-center bg-white/5 rounded-xl border border-white/10">
                        <div className="text-center text-gray-400">
                            <BarChart2 size={48} className="mx-auto mb-4 opacity-50" />
                            <p>数据可视化（开发中）</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default WorkspaceContainer;
