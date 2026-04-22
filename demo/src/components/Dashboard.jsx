import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  Brain, 
  Users, 
  Database, 
  Shield,
  Activity,
  Zap,
  DollarSign,
  AlertTriangle,
  FileText
} from 'lucide-react';
import MetricCard from './MetricCard';
import LiveChart from './LiveChart';
import ActivityFeed from './ActivityFeed';

const Dashboard = ({ setActiveSection }) => {
  const [metrics, setMetrics] = useState({
    totalProfit: 2847392.45,
    dailyReturn: 12.34,
    activeAgents: 12,
    dataPoints: 847392,
    riskScore: 23.5,
    executionSpeed: 0.003
  });

  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    const initialData = Array.from({ length: 50 }, (_, i) => ({
      time: Date.now() - (50 - i) * 1000,
      value: 100 + Math.random() * 50 - 25,
      volume: Math.random() * 1000000,
      sentiment: Math.random(),
    }));
    setChartData(initialData);

    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        totalProfit: prev.totalProfit + (Math.random() - 0.5) * 10000,
        dailyReturn: prev.dailyReturn + (Math.random() - 0.5) * 2,
        dataPoints: prev.dataPoints + Math.floor(Math.random() * 1000),
        riskScore: Math.max(0, Math.min(100, prev.riskScore + (Math.random() - 0.5) * 5)),
        executionSpeed: 0.001 + Math.random() * 0.005
      }));

      setChartData(prev => {
        const lastValue = prev.length > 0 ? prev[prev.length - 1].value : 100;
        const lastSentiment = prev.length > 0 ? prev[prev.length - 1].sentiment : 0.5;
        const newPoint = {
          time: Date.now(),
          value: lastValue + (Math.random() - 0.5) * 10,
          volume: Math.random() * 1000000,
          sentiment: Math.max(0, Math.min(1, lastSentiment + (Math.random() - 0.5) * 0.2)),
        };
        return [...prev.slice(1), newPoint];
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">PRIV Core Dashboard</h1>
          <p className="text-gray-400 mt-1">Real-time AI execution monitoring</p>
        </div>
        <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 font-medium">Live</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard title="Total Profit" value={`$${metrics.totalProfit.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} change={metrics.dailyReturn > 0 ? `+${metrics.dailyReturn.toFixed(2)}%` : `${metrics.dailyReturn.toFixed(2)}%`} icon={DollarSign} trend={metrics.dailyReturn > 0 ? 'up' : 'down'} color="green" />
        <MetricCard title="Daily Return" value={`${metrics.dailyReturn.toFixed(2)}%`} change="vs yesterday" icon={metrics.dailyReturn > 0 ? TrendingUp : TrendingDown} trend={metrics.dailyReturn > 0 ? 'up' : 'down'} color={metrics.dailyReturn > 0 ? 'green' : 'red'} />
        <MetricCard title="Active Agents" value={metrics.activeAgents.toString()} change="12/12 online" icon={Users} trend="stable" color="blue" onClick={() => setActiveSection('multi-agent')} />
        <MetricCard title="Data Points" value={metrics.dataPoints.toLocaleString()} change="+2.3k/min" icon={Database} trend="up" color="purple" onClick={() => setActiveSection('data-ingestion')} />
        <MetricCard title="Risk Score" value={`${metrics.riskScore.toFixed(1)}/100`} change="Low risk" icon={Shield} trend="stable" color="yellow" onClick={() => setActiveSection('security')} />
        <MetricCard title="Execution Speed" value={`${metrics.executionSpeed.toFixed(3)}s`} change="avg latency" icon={Zap} trend="stable" color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LiveChart data={chartData} />
        </div>
        
        <div className="space-y-6">
          <ActivityFeed />
          <div className="metric-card rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><Activity className="w-5 h-5 mr-2 text-green-400" />System Health</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between"><span className="text-gray-400">AGI Core</span><div className="flex items-center space-x-2"><div className="w-2 h-2 bg-green-400 rounded-full"></div><span className="text-green-400 text-sm">Optimal</span></div></div>
              <div className="flex items-center justify-between"><span className="text-gray-400">AI Core</span><div className="flex items-center space-x-2"><div className="w-2 h-2 bg-green-400 rounded-full"></div><span className="text-green-400 text-sm">Optimal</span></div></div>
              <div className="flex items-center justify-between"><span className="text-gray-400">Multi-Agent System</span><div className="flex items-center space-x-2"><div className="w-2 h-2 bg-green-400 rounded-full"></div><span className="text-green-400 text-sm">Active</span></div></div>
              <div className="flex items-center justify-between"><span className="text-gray-400">Security Layer</span><div className="flex items-center space-x-2"><div className="w-2 h-2 bg-green-400 rounded-full"></div><span className="text-green-400 text-sm">Secure</span></div></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div className="metric-card rounded-xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} >
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><AlertTriangle className="w-5 h-5 mr-2 text-yellow-400" />Recent Alerts</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20"><div className="flex items-center space-x-3"><div className="w-2 h-2 bg-yellow-400 rounded-full"></div><span className="text-white">High volatility detected in EUR/USD pair</span></div><span className="text-gray-400 text-sm">2 min ago</span></div>
              <div className="flex items-center justify-between p-3 bg-blue-500/10 rounded-lg border border-blue-500/20"><div className="flex items-center space-x-3"><div className="w-2 h-2 bg-blue-400 rounded-full"></div><span className="text-white">New arbitrage opportunity identified</span></div><span className="text-gray-400 text-sm">5 min ago</span></div>
              <div className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg border border-green-500/20"><div className="flex items-center space-x-3"><div className="w-2 h-2 bg-green-400 rounded-full"></div><span className="text-white">Risk model updated successfully</span></div><span className="text-gray-400 text-sm">12 min ago</span></div>
            </div>
        </motion.div>
        
        <motion.div className="metric-card rounded-xl p-6 cursor-pointer hover:border-blue-500/50" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} onClick={() => setActiveSection('tax')}>
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center"><FileText className="w-5 h-5 mr-2 text-blue-400" />Tax Intelligence Preview</h3>
            <p className="text-gray-400 mb-4 text-sm">Leveraging AGI to revolutionize tax compliance and revenue prediction for governments like GRA & SARS.</p>
            <div className="flex justify-between items-center text-sm">
                <span className="font-semibold text-blue-400">Revenue Forecast Accuracy</span>
                <span className="text-white font-bold">97.3%</span>
            </div>
             <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full w-[97.3%]"></div>
            </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
