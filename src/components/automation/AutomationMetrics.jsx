import React from 'react';
import { motion } from 'framer-motion';
import { Zap, CheckCircle, Activity, Settings, DollarSign, Bot } from 'lucide-react';

const Metric = ({ icon: Icon, value, label, subtext, color, delay }) => (
    <motion.div
        className={`metric-card rounded-xl p-4 border-${color}-500/20`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay }}
    >
        <div className="flex items-center justify-between mb-2">
            <Icon className={`w-5 h-5 text-${color}-400`} />
            <div className="text-right">
                <div className="text-xl font-bold text-white">{value}</div>
                <div className="text-xs text-gray-400">{label}</div>
            </div>
        </div>
        <div className={`text-xs text-${color}-400`}>{subtext}</div>
    </motion.div>
);

const AutomationMetrics = ({ metrics }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <Metric icon={Zap} value={metrics.totalTasks.toLocaleString()} label="Total Tasks" subtext={`+${metrics.completedToday} today`} color="green" delay={0} />
            <Metric icon={CheckCircle} value={`${metrics.successRate.toFixed(1)}%`} label="Success Rate" subtext="Excellent" color="blue" delay={0.1} />
            <Metric icon={Activity} value={`${metrics.avgExecutionTime.toFixed(3)}s`} label="Avg Execution" subtext="Ultra-fast" color="purple" delay={0.2} />
            <Metric icon={Settings} value={metrics.activeProcesses} label="Active Processes" subtext="Running" color="yellow" delay={0.3} />
            <Metric icon={DollarSign} value={metrics.savedHours.toLocaleString()} label="Hours Saved" subtext="This month" color="red" delay={0.4} />
            <Metric icon={Bot} value={metrics.moduleCount} label="AI Modules" subtext="All active" color="green" delay={0.5} />
        </div>
    );
};

export default AutomationMetrics;
