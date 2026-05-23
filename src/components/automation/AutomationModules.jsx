import React from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Wrench, Bot, Activity, FileText, Settings, Landmark } from 'lucide-react';
import { toast } from '../ui/use-toast';

const icons = { DollarSign, Wrench, Bot, Activity, FileText, Settings, Landmark };

const AutomationModules = ({ modules }) => {
    const handleModuleClick = (module) => {
        toast({
            title: `🤖 ${module.name} Details`,
            description: "This feature isn't implemented yet—but don't worry! You can request it in your next prompt! 🚀"
        });
    };

    const getStatusColor = (status) => ({
        active: 'text-green-400 bg-green-500/20 border-green-500/30',
        monitoring: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
        idle: 'text-gray-400 bg-gray-500/20 border-gray-500/30'
    }[status] || 'text-gray-400 bg-gray-500/20 border-gray-500/30');

    const getColorClasses = (color) => ({
        green: 'border-green-500/20 sans-glow',
        blue: 'border-blue-500/20 sans-glow-blue',
        purple: 'border-purple-500/20',
        yellow: 'border-yellow-500/20',
        red: 'border-red-500/20'
    }[color] || 'border-gray-500/20');

    return (
        <>
            {modules.map((module, index) => {
                const Icon = icons[module.icon];
                return (
                    <motion.div
                        key={module.id}
                        className={`metric-card rounded-xl p-6 cursor-pointer ${getColorClasses(module.color)}`}
                        whileHover={{ scale: 1.02, y: -4 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleModuleClick(module)}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center space-x-3">
                                <div className={`p-2 rounded-lg bg-${module.color}-500/20`}>
                                    <Icon className={`w-5 h-5 text-${module.color}-400`} />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-white">{module.name}</h3>
                                </div>
                            </div>
                            <div className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(module.status)}`}>{module.status}</div>
                        </div>
                        <p className="text-sm text-gray-400 mb-4 h-10">{module.description}</p>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm"><span className="text-gray-400">Efficiency</span><span className="font-medium text-white">{module.efficiency.toFixed(1)}%</span></div>
                            <div className="w-full bg-gray-700 rounded-full h-2">
                                <div className={`bg-gradient-to-r from-${module.color}-500 to-${module.color}-400 h-2 rounded-full`} style={{ width: `${module.efficiency}%` }}></div>
                            </div>
                            <div className="pt-2 border-t border-gray-700/50">
                                <p className="text-xs text-gray-400 mb-2">Key Features:</p>
                                <div className="flex flex-wrap gap-1">
                                    {module.features.slice(0, 2).map((feature, i) => <span key={i} className={`px-2 py-1 bg-${module.color}-500/20 text-${module.color}-400 text-xs rounded`}>{feature}</span>)}
                                    {module.features.length > 2 && <span className="text-xs text-gray-500">+{module.features.length - 2} more</span>}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                );
            })}
        </>
    );
};

export default AutomationModules;
