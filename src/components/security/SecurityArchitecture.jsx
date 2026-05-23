import React from 'react';
import { motion } from 'framer-motion';
import { Key, Lock, Shield, CheckCircle } from 'lucide-react';

const SecurityArchitecture = ({ securityMetrics }) => {
  return (
    <motion.div
      className="metric-card rounded-xl p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
    >
      <h3 className="text-lg font-semibold text-white mb-6">Security Architecture</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto border border-green-500/30">
            <Key className="w-8 h-8 text-green-400" />
          </div>
          <div>
            <h4 className="font-semibold text-white mb-2">Zero-Knowledge Proofs</h4>
            <p className="text-sm text-gray-400">Cryptographically prove integrity without revealing proprietary logic</p>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Verifications</span>
              <span className="text-green-400">{securityMetrics.zkpVerifications.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-1 rounded-full w-full"></div>
            </div>
          </div>
        </div>

        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto border border-blue-500/30">
            <Lock className="w-8 h-8 text-blue-400" />
          </div>
          <div>
            <h4 className="font-semibold text-white mb-2">Blockchain Logger</h4>
            <p className="text-sm text-gray-400">Immutable audit trail for all critical system actions</p>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Logs</span>
              <span className="text-blue-400">{securityMetrics.blockchainLogs.toLocaleString()}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-1 rounded-full w-full"></div>
            </div>
          </div>
        </div>

        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto border border-purple-500/30">
            <Shield className="w-8 h-8 text-purple-400" />
          </div>
          <div>
            <h4 className="font-semibold text-white mb-2">Post-Quantum Crypto</h4>
            <p className="text-sm text-gray-400">Future-proof encryption against quantum threats</p>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Strength</span>
              <span className="text-purple-400">{securityMetrics.encryptionStrength}-bit</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-1 rounded-full w-full"></div>
            </div>
          </div>
        </div>

        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto border border-yellow-500/30">
            <CheckCircle className="w-8 h-8 text-yellow-400" />
          </div>
          <div>
            <h4 className="font-semibold text-white mb-2">Compliance Engine</h4>
            <p className="text-sm text-gray-400">Automated regulatory compliance and ethical framework</p>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Score</span>
              <span className="text-yellow-400">{securityMetrics.complianceScore.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-1">
              <div className="bg-gradient-to-r from-yellow-500 to-orange-500 h-1 rounded-full w-[98.7%]"></div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default SecurityArchitecture;
