import React from 'react';
import Sidebar from './Sidebar';

const DashboardLayout = ({ children }) => {
    return (
        <div className="flex h-screen bg-background text-white font-sans selection:bg-primary/30 overflow-hidden">
            <Sidebar />
            <main className="flex-1 ml-20 relative h-full p-4">
                {/* Background ambient glow */}
                <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                    <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[100px]" />
                    <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[100px]" />
                </div>

                <div className="relative z-10 h-full">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default DashboardLayout;
