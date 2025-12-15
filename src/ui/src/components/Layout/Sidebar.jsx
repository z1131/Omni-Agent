import React from 'react';
import { MessageSquare, Box, Monitor, Settings, Cloud } from 'lucide-react';
import clsx from 'clsx';

const SidebarItem = ({ icon: Icon, label, active }) => (
    <div
        className={clsx(
            'flex items-center p-3 mb-2 rounded-xl transition-all duration-300 group cursor-pointer',
            active
                ? 'bg-primary/20 text-primary shadow-[0_0_15px_rgba(59,130,246,0.5)] border border-primary/30'
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
        )}
    >
        <Icon className="w-6 h-6" />
        <span className="ml-3 font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300 absolute left-16 bg-surface px-2 py-1 rounded border border-white/10 whitespace-nowrap z-50 pointer-events-none group-hover:block hidden">
            {label}
        </span>
    </div>
);

const Sidebar = () => {
    return (
        <div className="h-screen w-20 flex flex-col items-center py-6 bg-surface/50 backdrop-blur-xl border-r border-white/5 fixed left-0 top-0 z-50">
            <div className="mb-8">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent animate-pulse-slow flex items-center justify-center shadow-lg shadow-primary/20">
                    <span className="text-white font-bold text-lg">O</span>
                </div>
            </div>

            <nav className="flex-1 w-full px-2 flex flex-col items-center">
                <SidebarItem icon={MessageSquare} label="工作台" active={true} />
                <SidebarItem icon={Cloud} label="云环境" />
            </nav>

            <div className="w-full px-2 flex flex-col items-center">
                <SidebarItem icon={Settings} label="设置" />
            </div>
        </div>
    );
};

export default Sidebar;
