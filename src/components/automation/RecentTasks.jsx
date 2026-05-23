import React from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

const RecentTasks = ({ tasks }) => {
    const formatTime = (timestamp) => {
        const diff = Date.now() - timestamp;
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        if (minutes > 0) return `${minutes}m ago`;
        return `${seconds}s ago`;
    };

    return (
        <motion.div
            className="metric-card rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
        >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-green-400" />
                Recent Automated Tasks
            </h3>
            <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-hide">
                {tasks.map((task) => (
                    <motion.div
                        key={task.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`flex items-center justify-between p-3 rounded-lg border ${task.status === 'completed' ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}
                    >
                        <div className="flex items-center space-x-3">
                            <div className={`w-2 h-2 rounded-full ${task.status === 'completed' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                            <div>
                                <div className="text-sm text-white">{task.task}</div>
                                <div className="text-xs text-gray-400">{task.module}</div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm font-medium text-white">{task.duration.toFixed(2)}s</div>
                            <div className="text-xs text-gray-500">{formatTime(task.timestamp)}</div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    );
};

export default RecentTasks;
