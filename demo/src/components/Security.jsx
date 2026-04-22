import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Lock, Key, AlertTriangle, CheckCircle, Eye, Zap, X } from 'lucide-react';
import { Button } from './ui/button';
import SecurityArchitecture from './security/SecurityArchitecture';

const Security = () => {
  const [securityMetrics, setSecurityMetrics] = useState({ zkpVerifications: 15847, blockchainLogs: 2847, encryptionStrength: 256, threatLevel: 'Low', complianceScore: 98.7 });
  const [securityEvents, setSecurityEvents] = useState([]);
  const [threatMap, setThreatMap] = useState([]);
  const [modalContent, setModalContent] = useState(null);

  useEffect(() => {
    const events = [
      { id: 1, type: 'zkp_verification', message: 'Zero-knowledge proof verified for trade execution', severity: 'info', timestamp: Date.now() - 120000, icon: Key, color: 'green' },
      { id: 2, type: 'blockchain_log', message: 'Transaction logged to immutable blockchain', severity: 'info', timestamp: Date.now() - 180000, icon: Lock, color: 'blue' },
      { id: 3, type: 'compliance_check', message: 'Regulatory compliance validation passed', severity: 'success', timestamp: Date.now() - 240000, icon: CheckCircle, color: 'green' },
      { id: 4, type: 'threat_detected', message: 'Potential anomaly detected and mitigated', severity: 'warning', timestamp: Date.now() - 300000, icon: AlertTriangle, color: 'yellow' },
      { id: 5, type: 'encryption_update', message: 'Post-quantum cryptography keys rotated', severity: 'info', timestamp: Date.now() - 360000, icon: Shield, color: 'purple' }
    ];
    setSecurityEvents(events);

    const generateThreatMap = () => Array.from({ length: 50 }, (_, i) => ({ id: i, x: Math.random() * 100, y: Math.random() * 100, severity: Math.random(), type: ['intrusion', 'anomaly', 'compliance', 'fraud'][Math.floor(Math.random() * 4)] }));
    setThreatMap(generateThreatMap());

    const interval = setInterval(() => {
      setSecurityMetrics(prev => ({ ...prev, zkpVerifications: prev.zkpVerifications + Math.floor(Math.random() * 10 + 5), blockchainLogs: prev.blockchainLogs + Math.floor(Math.random() * 5 + 1), complianceScore: Math.max(95, Math.min(100, prev.complianceScore + (Math.random() - 0.5) * 2)) }));
      setThreatMap(generateThreatMap());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleSecurityFeatureClick = (feature) => {
    let content;
    switch(feature) {
      case 'Zero-Knowledge Proofs':
        content = { title: "Zero-Knowledge Proofs", description: "A ZKP has been verified for a high-value transaction. The proof's hash is `0x...a4b2`. This action is now cryptographically secured on the ledger without revealing any underlying trade logic." };
        break;
      case 'Blockchain Logger':
        content = { title: "Immutable Blockchain Logger", description: "A new block has been added to the audit trail. Block Height: 8,472,391. Transactions: 152. Hash: `0x...c8d4`. The integrity of all system actions is maintained." };
        break;
      case 'Compliance Audit':
        content = { title: "Simulated Compliance Audit", description: "Running a simulated audit... All 1,284 recent trades passed the ethical and regulatory framework checks. Compliance score remains at 98.7%. No violations found." };
        break;
      default:
        content = { title: feature, description: 'Live simulation data is being generated for this security module.' };
    }
    setModalContent(content);
  };
  
  const getSeverityColor = (severity) => ({ success: 'text-green-400 bg-green-500/20 border-green-500/30', info: 'text-blue-400 bg-blue-500/20 border-blue-500/30', warning: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30', error: 'text-red-400 bg-red-500/20 border-red-500/30' }[severity] || 'text-gray-400 bg-gray-500/20 border-gray-500/30');
  const formatTime = (timestamp) => `${Math.floor((Date.now() - timestamp) / 60000)}m ago`;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold gradient-text">Security & Governance</h1><p className="text-gray-400 mt-1">Unbreakable vault with quantum-resistant protection</p></div>
        <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30"><Shield className="w-5 h-5 text-green-400" /><span className="text-green-400 font-medium">Secure</span></div>
            <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30"><CheckCircle className="w-5 h-5 text-blue-400" /><span className="text-blue-400 font-medium">{securityMetrics.complianceScore.toFixed(1)}% Compliant</span></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <motion.div className="metric-card rounded-xl p-4 border-green-500/20 sans-glow cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => handleSecurityFeatureClick('Zero-Knowledge Proofs')}><div className="flex items-center justify-between mb-2"><Key className="w-5 h-5 text-green-400" /><div className="text-xl font-bold text-white">{securityMetrics.zkpVerifications.toLocaleString()}</div></div><p className="text-xs text-gray-400">ZKP Verifications</p></motion.div>
        <motion.div className="metric-card rounded-xl p-4 border-blue-500/20 sans-glow-blue cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => handleSecurityFeatureClick('Blockchain Logger')}><div className="flex items-center justify-between mb-2"><Lock className="w-5 h-5 text-blue-400" /><div className="text-xl font-bold text-white">{securityMetrics.blockchainLogs.toLocaleString()}</div></div><p className="text-xs text-gray-400">Blockchain Logs</p></motion.div>
        <motion.div className="metric-card rounded-xl p-4 border-purple-500/20 cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => handleSecurityFeatureClick('Post-Quantum Cryptography')}><div className="flex items-center justify-between mb-2"><Shield className="w-5 h-5 text-purple-400" /><div className="text-xl font-bold text-white">{securityMetrics.encryptionStrength}-bit</div></div><p className="text-xs text-gray-400">PQC Encryption</p></motion.div>
        <motion.div className="metric-card rounded-xl p-4 border-yellow-500/20 cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => handleSecurityFeatureClick('Threat Detection')}><div className="flex items-center justify-between mb-2"><AlertTriangle className="w-5 h-5 text-yellow-400" /><div className="text-xl font-bold text-white">{securityMetrics.threatLevel}</div></div><p className="text-xs text-gray-400">Threat Level</p></motion.div>
        <motion.div className="metric-card rounded-xl p-4 border-green-500/20 cursor-pointer" whileHover={{ scale: 1.05 }} onClick={() => handleSecurityFeatureClick('Compliance Audit')}><div className="flex items-center justify-between mb-2"><CheckCircle className="w-5 h-5 text-green-400" /><div className="text-xl font-bold text-white">{securityMetrics.complianceScore.toFixed(1)}%</div></div><p className="text-xs text-gray-400">Compliance</p></motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div className="metric-card rounded-xl p-6"><h3 className="text-lg font-semibold text-white mb-4 flex items-center"><Eye className="w-5 h-5 mr-2 text-red-400" />Real-time Threat Map</h3><div className="relative h-64 bg-black/50 rounded-lg overflow-hidden"><svg className="w-full h-full">{threatMap.map((t) => (<circle key={t.id} cx={`${t.x}%`} cy={`${t.y}%`} r={t.severity * 4 + 2} fill={t.severity > 0.7 ? '#ef4444' : t.severity > 0.4 ? '#f59e0b' : '#10b981'} opacity={t.severity * 0.8 + 0.2} className="animate-pulse" />))}</svg></div></motion.div>
        <motion.div className="metric-card rounded-xl p-6"><h3 className="text-lg font-semibold text-white mb-4 flex items-center"><Zap className="w-5 h-5 mr-2 text-yellow-400" />Security Events</h3><div className="space-y-3 max-h-64 overflow-y-auto scrollbar-hide">{securityEvents.map((e) => { const Icon = e.icon; return (<div key={e.id} className={`p-3 rounded-lg border ${getSeverityColor(e.severity)}`}><div className="flex items-start space-x-3"><Icon className={`w-4 h-4 mt-0.5 text-${e.color}-400`} /><div className="flex-1"><p className="text-sm text-white">{e.message}</p><span className="text-xs text-gray-500">{formatTime(e.timestamp)}</span></div></div></div>); })}</div></motion.div>
      </div>
      
      <SecurityArchitecture securityMetrics={securityMetrics} />

      <AnimatePresence>
        {modalContent && (
          <motion.div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="glass-morphism rounded-2xl w-full max-w-2xl p-8 border border-green-500/30" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}>
              <div className="flex justify-between items-start">
                <h2 className="text-2xl font-bold gradient-text mb-2">{modalContent.title}</h2>
                <Button variant="ghost" size="icon" onClick={() => setModalContent(null)}><X className="w-6 h-6" /></Button>
              </div>
              <p className="text-gray-300 mt-4 whitespace-pre-wrap font-mono text-sm">{modalContent.description}</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Security;
