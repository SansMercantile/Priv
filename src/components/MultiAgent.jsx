import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Brain, TrendingUp, Shield, Globe, Zap, AlertTriangle, CheckCircle, X, Bell, Workflow, PlayCircle } from 'lucide-react';
import { Button } from './ui/button';
import { orchestrationService } from '../services/orchestrationService';

const MultiAgent = ({ demoMode = false }) => {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedAgentVotes, setSelectedAgentVotes] = useState([]);
  const [selectedVoteDetail, setSelectedVoteDetail] = useState(null);
  const [arbitrationEvent, setArbitrationEvent] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [registryStatus, setRegistryStatus] = useState(null);
  const [workflowBusy, setWorkflowBusy] = useState(null);
  const [symbolInput, setSymbolInput] = useState('EURUSD,XAUUSD');

  const BACKEND_URL = import.meta.env.VITE_BACKEND_API_URL || '';

  const DEMO_AGENTS = [
      { agent_id: 'news-analysis-001', name: 'News Analysis Agent', type: 'analysis', status: 'active', performance: 95.5, reputation: 0.96, icon: Brain, color: 'purple', specialty: 'Real-time news & social sentiment', decisions: 127, accuracy: 95.5, lastAction: 'Processed 340 news items' },
      { agent_id: 'compliance-001', name: 'Compliance Agent', type: 'compliance', status: 'active', performance: 97.0, reputation: 0.97, icon: Shield, color: 'yellow', specialty: 'Compliance checks & controls', decisions: 220, accuracy: 97.0, lastAction: 'Performed AML checks' },
      { agent_id: 'arbitrage-001', name: 'Arbitrage Agent', type: 'arbitrage', status: 'monitoring', performance: 97.0, reputation: 0.97, icon: TrendingUp, color: 'green', specialty: 'Cross-market & triangular arbitrage', decisions: 1089, accuracy: 97.0, lastAction: 'Scanning for profit across 12 exchanges' },
      { agent_id: 'economic-001', name: 'Economic Agent', type: 'economic', status: 'active', performance: 92.0, reputation: 0.94, icon: Globe, color: 'blue', specialty: 'Macro & economic signals', decisions: 64, accuracy: 92.0, lastAction: 'Analyzed CPI release' },
      { agent_id: 'execution-001', name: 'Execution Agent', type: 'execution', status: 'active', performance: 96.0, reputation: 0.95, icon: Zap, color: 'green', specialty: 'Order routing & execution', decisions: 540, accuracy: 96.0, lastAction: 'Executed block trade' },
      { agent_id: 'political-001', name: 'Political Agent', type: 'political', status: 'active', performance: 90.0, reputation: 0.91, icon: Globe, color: 'blue', specialty: 'Geopolitical analysis', decisions: 15, accuracy: 90.0, lastAction: 'Flagged election risk' },
      { agent_id: 'portfolio-manager-001', name: 'Portfolio Manager Agent', type: 'portfolio_manager', status: 'active', performance: 94.0, reputation: 0.95, icon: Users, color: 'blue', specialty: 'Portfolio rebalancing & allocation', decisions: 324, accuracy: 94.0, lastAction: 'Rebalanced model portfolio' },
      { agent_id: 'quantitative-001', name: 'Quantitative Agent', type: 'quantitative', status: 'active', performance: 95.0, reputation: 0.95, icon: Brain, color: 'purple', specialty: 'Statistical models & signals', decisions: 410, accuracy: 95.0, lastAction: 'Updated predictive model' },
      { agent_id: 'risk-001', name: 'Risk Management Agent', type: 'risk', status: 'active', performance: 98.2, reputation: 0.98, icon: Shield, color: 'yellow', specialty: 'Portfolio risk & exposure', decisions: 89, accuracy: 98.2, lastAction: 'Adjusted VAR limits' },
      { agent_id: 'sentiment-001', name: 'Sentiment Agent', type: 'sentiment', status: 'active', performance: 91.0, reputation: 0.92, icon: Bell, color: 'orange', specialty: 'Social & sentiment signals', decisions: 402, accuracy: 91.0, lastAction: 'Detected rising social volume' },
      { agent_id: 'strategist-001', name: 'Strategist Agent', type: 'strategist', status: 'active', performance: 93.0, reputation: 0.94, icon: Users, color: 'blue', specialty: 'Strategy design & testing', decisions: 212, accuracy: 93.0, lastAction: 'Proposed new momentum strategy' },
      { agent_id: 'technical-001', name: 'Technical Analysis Agent', type: 'technical', status: 'active', performance: 94.1, reputation: 0.95, icon: Zap, color: 'green', specialty: 'Pattern recognition & indicators', decisions: 412, accuracy: 94.1, lastAction: 'Detected triple MA crossover' },
      { agent_id: 'commodity-001', name: 'Commodity Agent', type: 'commodity', status: 'monitoring', performance: 91.3, reputation: 0.90, icon: TrendingUp, color: 'yellow', specialty: 'Commodity market scans & fundamentals', decisions: 213, accuracy: 91.3, lastAction: 'Updated commodity exposure limits' },
      { agent_id: 'futures-001', name: 'Futures Agent', type: 'futures', status: 'active', performance: 93.7, reputation: 0.92, icon: TrendingUp, color: 'purple', specialty: 'Futures curves & roll analysis', decisions: 187, accuracy: 93.7, lastAction: 'Optimized roll strategy for NDX' },
      { agent_id: 'credit-001', name: 'Credit Agent', type: 'credit', status: 'active', performance: 90.5, reputation: 0.91, icon: Shield, color: 'yellow', specialty: 'Credit spreads & counterparty risk', decisions: 98, accuracy: 90.5, lastAction: 'Adjusted credit limits for ICE counterparties' },
      { agent_id: 'legal-001', name: 'Legal Compliance Agent', type: 'legal', status: 'active', performance: 99.5, reputation: 0.99, icon: AlertTriangle, color: 'red', specialty: 'Regulatory & compliance checks', decisions: 42, accuracy: 99.5, lastAction: 'Approved compliance for trade' },
      { agent_id: 'audit-001', name: 'Audit Agent', type: 'audit', status: 'active', performance: 92.5, reputation: 0.93, icon: CheckCircle, color: 'teal', specialty: 'Trade auditing & trails', decisions: 61, accuracy: 92.5, lastAction: 'Completed trade audit cycle' },
      { agent_id: 'ai-ops-001', name: 'AI-Ops Agent', type: 'ai_ops', status: 'active', performance: 90.5, reputation: 0.90, icon: Bell, color: 'yellow', specialty: 'Operational health & alerts', decisions: 120, accuracy: 90.5, lastAction: 'Published CPU alert' },
      { agent_id: 'research-001', name: 'Research Agent', type: 'research', status: 'active', performance: 92.0, reputation: 0.94, icon: Globe, color: 'blue', specialty: 'Fundamental & macro research', decisions: 64, accuracy: 92.0, lastAction: 'Generated macro report' },
      { agent_id: 'fomc-001', name: 'Policy/FOMC Watcher', type: 'fomc', status: 'monitoring', performance: 89.9, reputation: 0.89, icon: Globe, color: 'blue', specialty: 'Monetary policy & central bank signals', decisions: 55, accuracy: 89.9, lastAction: 'Flagged upcoming Fed release' },
      { agent_id: 'yield-optimizer-001', name: 'Yield Optimizer', type: 'yield_optimizer', status: 'active', performance: 91.5, reputation: 0.92, icon: TrendingUp, color: 'green', specialty: 'Yield curve strategies', decisions: 73, accuracy: 91.5, lastAction: 'Optimized muni curve position' },
      { agent_id: 'alt-data-001', name: 'Alternative Data Agent', type: 'alternative_data', status: 'active', performance: 90.0, reputation: 0.9, icon: Globe, color: 'blue', specialty: 'Alternative data signals', decisions: 131, accuracy: 90.0, lastAction: 'Ingested satellite data' },
      { agent_id: 'social-media-001', name: 'Social Media Agent', type: 'social_media', status: 'monitoring', performance: 88.5, reputation: 0.88, icon: Users, color: 'cyan', specialty: 'Social media & influencer tracking', decisions: 300, accuracy: 88.5, lastAction: 'Flagged trending thread' },
      { agent_id: 'tax-001', name: 'Tax Agent', type: 'tax', status: 'active', performance: 89.2, reputation: 0.89, icon: AlertTriangle, color: 'pink', specialty: 'Tax implications & optimization', decisions: 21, accuracy: 89.2, lastAction: 'Updated tax lots report' },
      { agent_id: 'ml-001', name: 'ML Agent', type: 'ml', status: 'active', performance: 92.5, reputation: 0.93, icon: Brain, color: 'purple', specialty: 'Model training & validation', decisions: 520, accuracy: 92.5, lastAction: 'Trained model v3.2' },
      { agent_id: 'options-001', name: 'Options Agent', type: 'options', status: 'monitoring', performance: 90.3, reputation: 0.9, icon: TrendingUp, color: 'teal', specialty: 'Options strategies & greeks', decisions: 88, accuracy: 90.3, lastAction: 'Rebalanced option exposure' },
      { agent_id: 'forex-001', name: 'Forex Agent', type: 'forex', status: 'active', performance: 91.7, reputation: 0.92, icon: Globe, color: 'blue', specialty: 'FX flows & carry trades', decisions: 135, accuracy: 91.7, lastAction: 'Updated FX exposure' },
      { agent_id: 'synthetic-markets-001', name: 'Synthetic Markets Agent', type: 'synthetic_markets', status: 'active', performance: 89.9, reputation: 0.9, icon: Zap, color: 'purple', specialty: 'Synthetic instruments & hedging', decisions: 47, accuracy: 89.9, lastAction: 'Hedged synthetic exposure' },
      { agent_id: 'sensory-001', name: 'Sensory Agent', type: 'sensory', status: 'monitoring', performance: 87.5, reputation: 0.88, icon: Globe, color: 'green', specialty: 'Real-world sensor data & context', decisions: 12, accuracy: 87.5, lastAction: 'Updated sensor feed' },
      { agent_id: 'reg-arbiter-001', name: 'Regulatory Arbiter', type: 'regulatory_arbiter', status: 'active', performance: 98.0, reputation: 0.99, icon: CheckCircle, color: 'indigo', specialty: 'Regulatory conflict resolution', decisions: 4, accuracy: 98.0, lastAction: 'Resolved reg dispute' },
      { agent_id: 'eth-arbiter-001', name: 'Ethical Arbiter', type: 'ethical_arbiter', status: 'active', performance: 97.5, reputation: 0.98, icon: CheckCircle, color: 'indigo', specialty: 'Ethical conflict resolution', decisions: 5, accuracy: 97.5, lastAction: 'Escalated ethical review' }
    ];

  useEffect(() => {
    if (demoMode) {
      setAgents(DEMO_AGENTS);
    } else {
      setAgents(DEMO_AGENTS.slice(0, 12));
    }
  }, [demoMode]);

  useEffect(() => {
    if (demoMode) return;
    let cancelled = false;

    const fetchLive = async () => {
      try {
        const [statusJson, registry] = await Promise.all([
          fetch(`${BACKEND_URL}/api/v1/agents/status_with_reputation`).then((r) => r.json()),
          orchestrationService.listRegistryAgents().catch(() => null),
        ]);
        const liveAgents = statusJson?.data?.agents || [];
        if (!cancelled && liveAgents.length) {
          const merged = liveAgents.map((a) => ({
            agent_id: a.id || a.agent_id,
            name: a.name,
            type: a.type || 'unknown',
            status: a.status || 'idle',
            performance: a.performance?.accuracy ?? a.performance ?? 0,
            reputation: a.reputation ?? 0.9,
            icon: Brain,
            color: 'blue',
            specialty: a.specialty || a.type,
            lastAction: a.last_activity || 'Active',
            decisions: a.tasks_completed || 0,
            accuracy: a.performance?.accuracy ?? 90,
          }));
          setAgents(merged);
        } else if (registry?.agents?.length && !cancelled) {
          setAgents(
            registry.agents.map((a) => ({
              agent_id: a.agent_id,
              name: a.agent_id,
              type: a.agent_type,
              status: a.status,
              performance: 90,
              reputation: 0.9,
              icon: Brain,
              color: 'purple',
              specialty: a.agent_type,
              lastAction: 'Registered',
              decisions: 0,
              accuracy: 90,
            }))
          );
        }
        if (registry && !cancelled) {
          const regStatus = await orchestrationService.getRegistryStatus();
          setRegistryStatus(regStatus);
        }
        const wf = await orchestrationService.listWorkflows();
        if (!cancelled) setWorkflows(wf?.workflows || []);
      } catch (err) {
        console.warn('Live agent fetch:', err.message);
      }
    };

    fetchLive();
    const poll = setInterval(fetchLive, 12000);
    return () => {
      cancelled = true;
      clearInterval(poll);
    };
  }, [demoMode, BACKEND_URL]);

  const startWorkflow = async (kind) => {
    if (demoMode) {
      setWorkflows([{ workflow_id: 'demo-wf', status: 'running', type: kind }]);
      return;
    }
    setWorkflowBusy(kind);
    try {
      const symbols = symbolInput.split(',').map((s) => s.trim()).filter(Boolean);
      let data;
      if (kind === 'trade') data = await orchestrationService.startTradeWorkflow(symbols);
      else if (kind === 'risk') data = await orchestrationService.startRiskWorkflow(symbols);
      else data = await orchestrationService.startNewsWorkflow();
      const wf = await orchestrationService.listWorkflows();
      setWorkflows(wf?.workflows || []);
      if (data?.workflow_id) {
        setArbitrationEvent({
          agent1: { name: 'Orchestrator' },
          agent2: { name: kind },
          decision1: `Started ${data.workflow_id}`,
          decision2: symbols.join(', ') || 'news',
          outcome: 'Workflow active',
        });
        setTimeout(() => setArbitrationEvent(null), 6000);
      }
    } catch (e) {
      console.error(e);
      alert(e.message || 'Workflow failed');
    } finally {
      setWorkflowBusy(null);
    }
  };

  const triggerArbitration = () => {
    const pool = agents.length ? agents : DEMO_AGENTS;
    setArbitrationEvent({
        agent1: pool[0],
        agent2: pool[2] || pool[1],
        decision1: 'Strong Buy Signal',
        decision2: 'High Bearish Sentiment',
        outcome: 'Escalated to C-Suite Agent'
    });
    setTimeout(() => setArbitrationEvent(null), 8000);
  };

  useEffect(() => {
    if (!demoMode) return;
    const interval = setInterval(() => {
      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          performance: Math.max(0, Math.min(100, agent.performance + (Math.random() - 0.5) * 2)),
          reputation: Math.max(0, Math.min(1, agent.reputation + (Math.random() - 0.5) * 0.02)),
        }))
      );
      if (Math.random() < 0.08) triggerArbitration();
    }, 5000);
    return () => clearInterval(interval);
  }, [demoMode, agents.length]);

  const handleAgentClick = (agent) => setSelectedAgent(agent);
  const handleCloseModal = () => {
    setSelectedAgent(null);
    setSelectedAgentVotes([]);
    setSelectedVoteDetail(null);
  };

  // Fetch last 3 votes for selected agent
  useEffect(() => {
    if (!selectedAgent) return;
    let cancelled = false;
    const fetchVotes = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/agents/${selectedAgent.agent_id}/votes?limit=3`);
        if (!res.ok) throw new Error(`Votes fetch failed: ${res.status}`);
        const json = await res.json();
        if (!cancelled) setSelectedAgentVotes(json?.data || []);
      } catch (err) {
        console.warn('Could not fetch votes for agent:', err.message);
      }
    };
    fetchVotes();
    return () => { cancelled = true; };
  }, [selectedAgent, BACKEND_URL]);

  const handleVoteClick = async (vote) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/agents/${selectedAgent.agent_id}/votes/${vote.vote_id}`);
      if (!res.ok) throw new Error(`Vote detail fetch failed: ${res.status}`);
      const json = await res.json();
      setSelectedVoteDetail(json?.data || null);
    } catch (err) {
      console.warn('Could not fetch vote detail:', err.message);
    }
  };

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
      <div className="metric-card rounded-xl p-6 border border-purple-500/20 mb-2">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Workflow className="w-5 h-5 text-purple-400" />
          Orchestration Control
        </h3>
        <p className="text-xs text-gray-400 mb-3 font-mono">
          {demoMode ? 'Demo — workflows are simulated' : 'POST /api/v1/orchestration/orchestration/*'}
        </p>
        <input
          value={symbolInput}
          onChange={(e) => setSymbolInput(e.target.value)}
          className="w-full mb-3 p-2 rounded bg-black/40 border border-white/10 text-white text-xs font-mono"
          placeholder="Symbols: EURUSD, XAUUSD"
        />
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'trade', label: 'Trade workflow' },
            { id: 'risk', label: 'Risk workflow' },
            { id: 'news', label: 'News workflow' },
          ].map(({ id, label }) => (
            <button
              key={id}
              type="button"
              disabled={workflowBusy != null}
              onClick={() => startWorkflow(id)}
              className="flex items-center gap-1 px-3 py-2 rounded border border-purple-500/30 text-xs font-mono text-purple-200 hover:bg-purple-500/10 disabled:opacity-50"
            >
              <PlayCircle className="w-3.5 h-3.5" />
              {workflowBusy === id ? 'Starting…' : label}
            </button>
          ))}
        </div>
        {registryStatus && !demoMode && (
          <p className="text-[10px] font-mono text-gray-500 mt-3">
            Registry: {registryStatus.total_agents ?? '—'} agents · broker connected:{' '}
            {String(registryStatus.broker_status?.connected ?? false)}
          </p>
        )}
        {workflows.length > 0 && (
          <ul className="mt-3 space-y-1 text-[10px] font-mono text-gray-400">
            {workflows.slice(0, 5).map((w, i) => (
              <li key={i}>
                {w.workflow_id || w.id} — {w.status || w.state || 'active'}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Multi-Agent Ecosystem</h1>
          <p className="text-gray-400 mt-1">
            {demoMode ? 'Demo agent roster with simulated metrics' : 'Live agents + orchestration registry'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30"><CheckCircle className="w-5 h-5 text-green-400" /><span className="text-green-400 font-medium">{agents.filter(a => a.status === 'active').length} Active</span></div>
          <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30"><Users className="w-5 h-5 text-blue-400" /><span className="text-blue-400 font-medium">{agents.length} Total Agents</span></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent, index) => {
          const Icon = agent.icon;
          const keyId = agent.agent_id || agent.id || index;
          return (
            <motion.div key={keyId} className={`metric-card rounded-xl p-6 cursor-pointer ${getColorClasses(agent.color)}`} whileHover={{ scale: 1.02, y: -4 }} whileTap={{ scale: 0.98 }} onClick={() => handleAgentClick(agent)} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: index * 0.05 }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3"><div className={`p-2 rounded-lg bg-${agent.color}-500/20`}><Icon className={`w-5 h-5 text-${agent.color}-400`} /></div><div><h3 className="font-semibold text-white">{agent.name}</h3><p className="text-xs text-gray-400">{agent.type}</p></div></div>
                <div className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(agent.status)}`}>{agent.status}</div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center"><span className="text-sm text-gray-400">Performance</span><span className="text-sm font-medium text-white">{agent.performance.toFixed(1)}%</span></div>
                <div className="w-full bg-gray-700 rounded-full h-2"><div className={`bg-gradient-to-r from-${agent.color}-500 to-${agent.color}-400 h-2 rounded-full`} style={{ width: `${agent.performance}%` }}></div></div>
                <div className="flex justify-between items-center"><span className="text-sm text-gray-400">Reputation</span><span className="text-sm font-medium text-white">{(agent.reputation ?? 0).toFixed(2)}</span></div>
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
              {agents.slice(0, 3).map((agent, i) => { const Icon = agent.icon; const keyId = agent.agent_id || agent.id || i; return (
                  <div key={keyId} className={`flex items-start space-x-4 p-3 bg-${agent.color}-500/10 rounded-lg border border-${agent.color}-500/20`}>
                    <Icon className={`w-5 h-5 text-${agent.color}-400 mt-0.5`} />
                    <div className="flex-1"><div className="text-white font-medium text-sm">{agent.name}</div><div className="text-gray-400 text-xs mt-1">{agent.lastAction}</div></div>
                  </div>
              );})}
            </div>
        </motion.div>

        {/* Reputation Ledger panel */}
        <motion.div className="metric-card rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.45 }}>
            <h3 className="text-lg font-semibold text-white mb-4">Agent Reputation Ledger</h3>
            <div className="space-y-3">
              {agents.slice(0).sort((a,b)=> (b.reputation||0) - (a.reputation||0)).slice(0,6).map((agent, idx) => (
                <div key={agent.agent_id || agent.id || idx} className="flex items-center justify-between p-2 bg-black/20 rounded-lg">
                  <div className="flex items-center gap-3"><div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm font-semibold">{agent.name.split(' ').map(n=>n[0]).slice(0,2).join('')}</div><div><div className="text-white font-medium text-sm">{agent.name}</div><div className="text-gray-400 text-xs">{agent.type}</div></div></div>
                  <div className="text-right"><div className="text-white font-bold">{((agent.reputation||0)*100).toFixed(0)}%</div><div className="text-gray-400 text-xs">score</div></div>
                </div>
              ))}
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
                        <h4 className="font-semibold text-white mb-4">Recent Votes</h4>
                        {selectedAgentVotes && selectedAgentVotes.length ? (
                          <div className="space-y-2">
                            {selectedAgentVotes.map(v => (
                              <div key={v.vote_id} className="p-2 bg-black/20 rounded-lg flex items-center justify-between">
                                <div>
                                  <div className="text-white font-medium">{v.vote} <span className="text-gray-400 text-xs">({v.confidence})</span></div>
                                  <div className="text-gray-400 text-xs">{new Date(v.timestamp).toLocaleString()}</div>
                                </div>
                                <div>
                                  <Button variant="ghost" size="sm" onClick={() => handleVoteClick(v)}>Details</Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500">No recent recorded votes.</p>
                        )}

                        {selectedVoteDetail && (
                          <div className="mt-4 p-3 bg-gray-900 rounded-lg border border-gray-700">
                            <div className="flex justify-between items-start"><div><div className="text-white font-medium">Vote: {selectedVoteDetail.vote} <span className="text-gray-400 text-xs">({selectedVoteDetail.confidence})</span></div><div className="text-gray-400 text-xs">{new Date(selectedVoteDetail.timestamp).toLocaleString()}</div></div><Button variant="ghost" size="icon" onClick={() => setSelectedVoteDetail(null)}><X className="w-4 h-4" /></Button></div>
                            <div className="text-gray-300 text-sm mt-2">{selectedVoteDetail.reasoning}</div>
                          </div>
                        )}
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
