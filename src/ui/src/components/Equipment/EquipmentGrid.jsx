import React, { useState, useEffect } from 'react';
import { Search, Filter, Globe, Code, FileText, Image, Database, Terminal } from 'lucide-react';
import clsx from 'clsx';
import EquipmentCard from './EquipmentCard';

const initialTools = [];

const EquipmentGrid = ({ compact = false }) => {
    const [tools, setTools] = useState(initialTools);
    const [search, setSearch] = useState('');
    const [filter, setFilter] = useState('全部');

    useEffect(() => {
        fetch('http://localhost:8000/tools')
            .then(res => res.json())
            .then(data => {
                // Map backend tool IDs to icons if needed, or just use defaults
                // For simplicity, we'll just try to match by name or category if we want specific icons,
                // or just default based on category. 
                // Since the backend returns 'id', 'name', 'category', we can try to map icons here.
                const iconMap = {
                    'Research': Globe,
                    'Development': Terminal,
                    'Creative': Image,
                    'Utility': FileText,
                    'Data': Database,
                    'File Operations': FileText,
                    'General': Code
                };

                const toolsWithIcons = data.tools.map(t => ({
                    ...t,
                    // Support both 'enabled' (new API) and 'installed' (old API) field names
                    installed: t.enabled !== undefined ? t.enabled : t.installed,
                    icon: iconMap[t.category] || Code
                }));
                setTools(toolsWithIcons);
            })
            .catch(err => console.error("Failed to load tools", err));
    }, []);

    const handleInstall = (id) => {
        const tool = tools.find(t => t.id === id);
        if (!tool) return;

        // Optimistic update
        setTools(tools.map(t => t.id === id ? { ...t, installed: true } : t));

        fetch('http://localhost:8000/tools/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_id: id, install: true })
        }).catch(err => {
            console.error("Install failed", err);
            // Revert
            setTools(tools.map(t => t.id === id ? { ...t, installed: false } : t));
        });
    };

    const handleUninstall = (id) => {
        const tool = tools.find(t => t.id === id);
        if (!tool) return;

        setTools(tools.map(t => t.id === id ? { ...t, installed: false } : t));

        fetch('http://localhost:8000/tools/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tool_id: id, install: false })
        }).catch(err => {
            console.error("Uninstall failed", err);
            setTools(tools.map(t => t.id === id ? { ...t, installed: true } : t));
        });
    };

    const filteredTools = tools.filter(t =>
        (filter === '全部' || t.category === filter) &&
        (t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()))
    );

    const categories = ['全部', ...new Set(tools.map(t => t.category))];

    return (
        <div className="flex flex-col h-full">
            {/* Toolbar */}
            {!compact && (
                <div className="flex flex-col md:flex-row justify-between items-center mb-8 space-y-4 md:space-y-0">
                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={18} />
                        <input
                            type="text"
                            placeholder="搜索工具..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full bg-surface border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50 focus:shadow-[0_0_15px_rgba(59,130,246,0.1)] transition-all"
                        />
                    </div>

                    <div className="flex space-x-2 overflow-x-auto w-full md:w-auto pb-2 md:pb-0">
                        {categories.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setFilter(cat)}
                                className={`px-4 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${filter === cat
                                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                                    : 'bg-surface text-gray-400 hover:text-white hover:bg-white/10'
                                    }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Grid */}
            <div className={clsx(
                'grid gap-4 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent',
                compact ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
            )}>
                {filteredTools.map(tool => (
                    <EquipmentCard
                        key={tool.id}
                        tool={tool}
                        onInstall={handleInstall}
                        onUninstall={handleUninstall}
                    />
                ))}
            </div>
        </div>
    );
};

export default EquipmentGrid;
