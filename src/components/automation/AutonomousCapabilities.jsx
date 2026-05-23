import React from 'react';
import { motion } from 'framer-motion';
import { DollarSign, Wrench, Bot, Activity } from 'lucide-react';

const Capability = ({ icon: Icon, title, description, metricLabel, metricValue, color, width }) => (
    <div className="text-center space-y-4">
        <div className={`w-16 h-16 bg-${color}-500/20 rounded-full flex items-center justify-center mx-auto border border-${color}-500/30`}>
            <Icon className={`w-8 h-8 text-${color}-400`} />
        </div>
        <div>
            <h4 className="font-semibold text-white mb-2">{title}</h4>
            <p className="text-sm text-gray-400 h-20">{description}</p>
        </div>
        <div className="space-y-2">
            <div className="flex justify-between text-xs">
                <span className="text-gray-400">{metricLabel}</span>
                <span className={`text-${color}-400`}>{metricValue}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
                <div className={`bg-gradient-to-r from-${color}-500 to-${color}-400 h-1 rounded-full`} style={{ width }}></div>
            </div>
        </div>
    </div>
);

const AutonomousCapabilities = () => {
    const capabilities = [
        { icon: DollarSign, title: "Financial Operations", description: "Complete automation of AP/AR, FP&A, and tax compliance.", metricLabel: "Automation Level", metricValue: "98.7%", color: "green", width: "98.7%" },
        { icon: Wrench, title: "Self-Healing", description: "Autonomous updates, error recovery, and performance optimization.", metricLabel: "Uptime", metricValue: "99.8%", color: "blue", width: "99.8%" },
        { icon: Bot, title: "AI Testing", description: "Secure sandbox for strategy validation and backtesting before live deployment.", metricLabel: "Active Tests", metricValue: "3", color: "purple", width: "75%" },
        { icon: Activity, title: "Support AI", description: "Intelligent, context-aware user support and real-time market insights.", metricLabel: "Response Time", metricValue: "0.3s", color: "yellow", width: "95%" }
    ];

    return (
        <motion.div
            className="metric-card rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
        >
            <h3 className="text-lg font-semibold text-white mb-6">Autonomous Capabilities</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {capabilities.map((cap, index) => (
                    <Capability key={index} {...cap} />
                ))}
            </div>
        </motion.div>
    );
};

export default AutonomousCapabilities;
