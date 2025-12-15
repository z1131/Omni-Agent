import React from 'react';
import WorkspaceContainer from '../components/Workspace/WorkspaceContainer';

const WorkspacePage = () => {
    return (
        <div className="h-full p-6 md:p-10 flex flex-col">
            <div className="mb-6">
                <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Workspace</h1>
                <p className="text-gray-400">Collaborate with Omni-Agent on complex tasks.</p>
            </div>

            <div className="flex-1 min-h-0">
                <WorkspaceContainer />
            </div>
        </div>
    );
};

export default WorkspacePage;
