import React from 'react';
import EquipmentGrid from '../components/Equipment/EquipmentGrid';

const EquipmentPage = () => {
    return (
        <div className="h-full p-6 md:p-10 flex flex-col">
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Equipment Library</h1>
                <p className="text-gray-400">Install and manage capabilities for your Omni-Agent.</p>
            </div>

            <div className="flex-1 min-h-0">
                <EquipmentGrid />
            </div>
        </div>
    );
};

export default EquipmentPage;
