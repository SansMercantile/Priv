import React from 'react';
import { motion } from 'framer-motion';
import { Wrench, CheckCircle, Activity, Bot, DollarSign, Settings } from 'lucide-react';

const HealthItem = ({ icon: Icon, label, status, color }) => (
    <div className={`flex items-center justify-between p-3 bg-${color}-500/10 rounded-lg border border-${color}-500/20`}>
        <div className="flex items-center space-x-3">
            <Icon className={`w-5 h-5 text-${color}-400`} />
            <span className="text-white">{label}</span>
        </div>
        <span className={`text-${color}-400 text-sm`}>{status}</span>
    </div>
);

const SystemHealth = () => {
    const healthItems = [
        { icon: CheckCircle, label: "Self-Healing System", status: "Optimal", color: "green" },
        { icon: Activity, label: "Resource Utilization", status: "67%", color: "blue" },
        { icon: Bot, label: "AI Sandbox", status: "Testing 3 strategies", color: "purple" },
        { icon: DollarSign, label: "Financial Automation", status: "Processing", color: "yellow" },
        { icon: Settings, label: "System Updates", status: "Up to date", color: "green" }
    ];

    return (
        <motion.div
            className="metric-card rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
        >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Wrench className="w-5 h-5 mr-2 text-blue-400" />
                System Health Monitor
            </h3>
            <div className="space-y-4">
                {healthItems.map((item, index) => (
                    <HealthItem key={index} {...item} />
                ))}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-700">
                <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Overall Health</span>
                    <span className="text-green-400">98.7%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full w-[98.7%]"></div>
                </div>
            </div>
        </motion.div>
    );
};

export default SystemHealth;
