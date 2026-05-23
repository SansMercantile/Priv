import React from 'react';
import { motion } from 'framer-motion';
import { Landmark } from 'lucide-react';

const TaxAutomationPreview = () => {
    return (
        <motion.div
            className="metric-card rounded-xl p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
        >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Landmark className="w-5 h-5 mr-2 text-blue-400" />
                Tax Automation (SARS & GRA)
            </h3>
            <p className="text-sm text-gray-400 mb-4">
                Full automation of tax reporting for South African (SARS) and Ghanaian (GRA) compliance.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
                    <p className="text-xs text-blue-400">SARS eFiling Status</p>
                    <p className="text-lg font-bold text-white">Submitted</p>
                    <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
                <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
                    <p className="text-xs text-green-400">GRA Reporting</p>
                    <p className="text-lg font-bold text-white">Pending</p>
                    <p className="text-xs text-gray-500">Next run in 4 hours</p>
                </div>
                <div className="p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                    <p className="text-xs text-yellow-400">Compliance Score</p>
                    <p className="text-lg font-bold text-white">99.5%</p>
                    <p className="text-xs text-gray-500">Real-time</p>
                </div>
            </div>
        </motion.div>
    );
};

export default TaxAutomationPreview;
