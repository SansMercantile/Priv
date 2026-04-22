import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Brain, TrendingUp, Shield, Globe, Zap, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { Button } from './ui/button';

const MultiAgent = () => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [arbitrationEvent, setArbitrationEvent] = useState(null);

  useEffect(() => {
    const initialAgents = [
      { id: 1, name: 'Quant-Alpha-7', type: 'Quantitative', status: 'active', performance: 94.2, reputation: 0.97, icon: TrendingUp, color: 'green', specialty: 'Statistical Arbitrage', decisions: 1247, accuracy: 89.3, lastAction: 'Identified mean reversion opportunity in EURUSD' },
      { id: 2, name: 'Risk-Guardian', type: 'Risk Management', status: 'active', performance: 91.8, reputation: 0.95, icon: Shield, color: 'yellow', specialty: 'Portfolio Risk Assessment', decisions: 892, accuracy: 94.7, lastAction: 'Reduced position size due to volatility spike' },
      { id: 3, name: 'Sentiment-Oracle', type: 'Sentiment Analysis', status: 'active', performance: 87.5, reputation: 0.89, icon: Brain, color: 'purple', specialty: 'Social Media & News Analysis', decisions: 2156, accuracy: 82.1, lastAction: 'Detected bearish sentiment shift in crypto markets' },
      { id: 4, name: 'Macro-Strategist', type: 'Economic Analysis', status: 'active', performance: 96.1, reputation: 0.98, icon: Globe, color: 'blue', specialty: 'Macroeconomic Forecasting', decisions: 634, accuracy: 91.8, lastAction: 'Updated inflation expectations model' },
      { id: 5, name: 'Execution-Lightning', type: 'Trade Execution', status: 'active', performance: 99.2, reputation: 0.99, icon: Zap, color: 'red', specialty: 'High-Frequency Execution', decisions: 15847, accuracy: 99.1, lastAction: 'Executed 247 trades with 0.002s avg latency' },
      { id: 6, name: 'Arbitrage-Hunter', type: 'Arbitrage', status: 'monitoring', performance: 88.9, reputation: 0.92, icon: TrendingUp, color: 'green', specialty: 'Cross-Market Arbitrage', decisions: 1089, accuracy: 95.4, lastAction: 'Monitoring price discrepancies across 12 exchanges' }
    ];
    setAgents(initialAgents);

    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({ ...agent, performance: Math.max(0, Math.min(100, agent.performance + (Math.random() - 0.5) * 2)), reputation: Math.max(0, Math.min(1, agent.reputation + (Math.random() - 0.5) * 0.02)) })));
      if (Math.random() < 0.1) {
        triggerArbitration();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);
  
  const triggerArbitration = () => {
    setArbitrationEvent({
        agent1: agents[0],
        agent2: agents[2],
        decision1: 'Strong Buy Signal',
        decision2: 'High Bearish Sentiment',
        outcome: 'Escalated to C-Suite Agent'
    });
    setTimeout(() => setArbitrationEvent(null), 8000);
  };

  const handleAgentClick = (agent) => setSelectedAgent(agent);
  const handleCloseModal = () => setSelectedAgent(null);

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'monitoring': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/30';
    }
  };

  const getColorClasses = (color) => {
    const colors = { green: 'border-green-500/20 sans-glow', blue: 'border-blue-500/20 sans-glow-blue', purple: 'border-purple-500/20', yellow: 'border-yellow-500/20', red: 'border-red-500/20' };
    return colors[color] || colors.green;
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Multi-Agent Ecosystem</h1>
          <p className="text-gray-400 mt-1">Decentralized fleet of specialized AI agents</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30"><CheckCircle className="w-5 h-5 text-green-400" /><span className="text-green-400 font-medium">{agents.filter(a => a.status === 'active').length} Active</span></div>
          <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30"><Users className="w-5 h-5 text-blue-400" /><span className="text-blue-400 font-medium">{agents.length} Total Agents</span></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => {
          const Icon = agent.icon;
          return (
            <motion.div key={agent.id} className={`metric-card rounded-xl p-6 cursor-pointer ${getColorClasses(agent.color)}`} whileHover={{ scale: 1.02, y: -4 }} whileTap={{ scale: 0.98 }} onClick={() => handleAgentClick(agent)} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: agent.id * 0.1 }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3"><div className={`p-2 rounded-lg bg-${agent.color}-500/20`}><Icon className={`w-5 h-5 text-${agent.color}-400`} /></div><div><h3 className="font-semibold text-white">{agent.name}</h3><p className="text-xs text-gray-400">{agent.type}</p></div></div>
                <div className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(agent.status)}`}>{agent.status}</div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center"><span className="text-sm text-gray-400">Performance</span><span className="text-sm font-medium text-white">{agent.performance.toFixed(1)}%</span></div>
                <div className="w-full bg-gray-700 rounded-full h-2"><div className={`bg-gradient-to-r from-${agent.color}-500 to-${agent.color}-400 h-2 rounded-full`} style={{ width: `${agent.performance}%` }}></div></div>
                <div className="flex justify-between items-center"><span className="text-sm text-gray-400">Reputation</span><span className="text-sm font-medium text-white">{agent.reputation.toFixed(2)}</span></div>
                <div className="pt-2 border-t border-gray-700"><p className="text-xs text-gray-400 mb-1">Specialty:</p><p className="text-sm text-white">{agent.specialty}</p></div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div className="metric-card rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><Users className="w-5 h-5 mr-2 text-blue-400" />Agent Communication Network</h3>
          <div className="relative h-64 bg-black/50 rounded-lg overflow-hidden flex items-center justify-center">
            {arbitrationEvent ? (
                <motion.div initial={{opacity: 0, scale: 0.8}} animate={{opacity: 1, scale: 1}} className="text-center">
                    <h4 className="text-yellow-400 font-bold mb-2">ARBITRATION EVENT</h4>
                    <p className="text-sm text-gray-300">{arbitrationEvent.agent1.name} vs {arbitrationEvent.agent2.name}</p>
                    <p className="text-lg font-bold text-white my-4">"{arbitrationEvent.decision1}" vs "{arbitrationEvent.decision2}"</p>
                    <p className="text-green-400">Outcome: {arbitrationEvent.outcome}</p>
                </motion.div>
            ) : (
                <p className="text-gray-500">Monitoring agent communications...</p>
            )}
          </div>
        </motion.div>
        <motion.div className="metric-card rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.4 }} >
            <h3 className="text-lg font-semibold text-white mb-4">Recent Agent Activities</h3>
            <div className="space-y-4">
              {agents.slice(0, 3).map((agent) => { const Icon = agent.icon; return (
                  <div key={agent.id} className={`flex items-start space-x-4 p-3 bg-${agent.color}-500/10 rounded-lg border border-${agent.color}-500/20`}>
                    <Icon className={`w-5 h-5 text-${agent.color}-400 mt-0.5`} />
                    <div className="flex-1"><div className="text-white font-medium text-sm">{agent.name}</div><div className="text-gray-400 text-xs mt-1">{agent.lastAction}</div></div>
                  </div>
              );})}
            </div>
        </motion.div>
      </div>

      <AnimatePresence>
        {selectedAgent && (
          <motion.div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="glass-morphism rounded-2xl w-full max-w-2xl p-8 border border-green-500/30" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }}>
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold gradient-text mb-2">{selectedAgent.name}</h2>
                        <p className="text-gray-400">{selectedAgent.type} Agent / {selectedAgent.specialty}</p>
                    </div>
                    <Button variant="ghost" size="icon" onClick={handleCloseModal}><X className="w-6 h-6" /></Button>
                </div>
                <div className="mt-6 grid grid-cols-2 gap-6">
                    <div>
                        <h4 className="font-semibold text-white mb-4">Live Metrics</h4>
                        <p className="text-gray-400">Performance: <span className="text-green-400">{selectedAgent.performance.toFixed(1)}%</span></p>
                        <p className="text-gray-400">Reputation: <span className="text-blue-400">{selectedAgent.reputation.toFixed(2)}</span></p>
                        <p className="text-gray-400">Accuracy: <span className="text-purple-400">{selectedAgent.accuracy}%</span></p>
                        <p className="text-gray-400">Decisions Made: <span className="text-white">{selectedAgent.decisions.toLocaleString()}</span></p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-white mb-4">Agent Activity Log</h4>
                        <p className="text-gray-500 text-sm">Simulating live activity...</p>
                        <p className="text-gray-400 text-sm mt-2">`[3s ago]` - {selectedAgent.lastAction}</p>
                        <p className="text-gray-400 text-sm mt-1">`[1m ago]` - Analyzed 1.2M data points.</p>
                        <p className="text-gray-400 text-sm mt-1">`[3m ago]` - Collaborated with Risk-Guardian.</p>
                    </div>
                </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MultiAgent;
