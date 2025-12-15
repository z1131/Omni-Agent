import React from 'react';
import clsx from 'clsx';
import { Download, Check, Settings, Trash2 } from 'lucide-react';

const EquipmentCard = ({ tool, onInstall, onUninstall }) => {
    const { id, name, description, icon: Icon, installed, category } = tool;

    return (
        <div className="bg-surface border border-white/5 rounded-2xl p-5 hover:border-primary/50 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-300 group relative overflow-hidden flex flex-col h-full">
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-white/5 to-transparent rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-500" />

            <div className="flex items-start justify-between mb-4 relative z-10">
                <div className={clsx(
                    'w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300',
                    installed ? 'bg-secondary/20 text-secondary' : 'bg-white/5 text-gray-400 group-hover:bg-primary/20 group-hover:text-primary'
                )}>
                    <Icon size={24} />
                </div>
                {installed && (
                    <div className="bg-secondary/20 text-secondary text-[10px] font-bold px-2 py-1 rounded-full flex items-center">
                        <Check size={10} className="mr-1" />
                        已启用
                    </div>
                )}
            </div>

            <div className="flex-1 relative z-10">
                <h3 className="text-lg font-bold text-white mb-1 group-hover:text-primary transition-colors">{name}</h3>
                <p className="text-xs text-gray-500 mb-2 uppercase tracking-wider">{category}</p>
                <p className="text-sm text-gray-400 leading-relaxed line-clamp-3">{description}</p>
            </div>

            <div className="mt-6 relative z-10">
                {installed ? (
                    <div className="flex space-x-2">
                        <button className="flex-1 bg-white/5 hover:bg-white/10 text-white py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center">
                            <Settings size={16} className="mr-2" />
                            配置
                        </button>
                        <button
                            onClick={() => onUninstall(id)}
                            className="w-10 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg flex items-center justify-center transition-colors"
                        >
                            <Trash2 size={16} />
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => onInstall(id)}
                        className="w-full bg-white/5 hover:bg-primary hover:text-white text-gray-300 py-2 rounded-lg text-sm font-medium transition-all duration-300 flex items-center justify-center group-hover:shadow-lg group-hover:shadow-primary/25"
                    >
                        <Download size={16} className="mr-2" />
                        启用
                    </button>
                )}
            </div>
        </div>
    );
};

export default EquipmentCard;
