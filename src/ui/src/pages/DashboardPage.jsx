import React from 'react';
import ChatWindow from '../components/Chat/ChatWindow';
import EquipmentPanel from '../components/Equipment/EquipmentPanel';
import WorkspaceContainer from '../components/Workspace/WorkspaceContainer';

const DashboardPage = () => {
    return (
        <div className="grid grid-cols-2 grid-rows-2 gap-4 h-full">
            {/* Left Pane: Conversation (Spans 2 rows) */}
            <div className="col-span-1 row-span-2 bg-surface/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl flex flex-col">
                <div className="p-4 border-b border-white/5 bg-white/5">
                    <h2 className="text-lg font-bold text-white flex items-center">
                        <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                        对话
                    </h2>
                </div>
                <div className="flex-1 min-h-0">
                    <ChatWindow compact={true} />
                </div>
            </div>

            {/* Top Right Pane: Equipment Library */}
            <div className="col-span-1 row-span-1 bg-surface/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl flex flex-col">
                <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
                    <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">工具库</h2>
                </div>
                <div className="flex-1 min-h-0 p-2">
                    <EquipmentPanel compact={true} />
                </div>
            </div>

            {/* Bottom Right Pane: Workspace */}
            <div className="col-span-1 row-span-1 bg-surface/50 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl flex flex-col">
                <div className="p-3 border-b border-white/5 bg-white/5 flex justify-between items-center">
                    <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider">工作区</h2>
                </div>
                <div className="flex-1 min-h-0 p-2">
                    <WorkspaceContainer compact={true} />
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
