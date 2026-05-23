import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Brain, Users, Database, Shield, Zap } from 'lucide-react';

const ActivityFeed = () => {
  const [activities, setActivities] = useState([]);

  const activityTypes = [
    { type: 'agi', icon: Brain, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
    { type: 'agent', icon: Users, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    { type: 'data', icon: Database, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
    { type: 'security', icon: Shield, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
    { type: 'execution', icon: Zap, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' }
  ];

  const generateActivity = () => {
    const activities = [
      { type: 'agi', message: 'AGI Core processed emotional sentiment analysis', agent: 'Empathy Engine' },
      { type: 'agent', message: 'Quantitative Agent identified arbitrage opportunity', agent: 'Quant-Alpha-7' },
      { type: 'data', message: 'Ingested 2.3K new market data points', agent: 'Data Fusion' },
      { type: 'security', message: 'Zero-knowledge proof verification completed', agent: 'ZKP Verifier' },
      { type: 'execution', message: 'High-frequency trade executed in 0.002s', agent: 'Execution Engine' },
      { type: 'agi', message: 'Unified Consciousness updated strategy weights', agent: 'AGI Core' },
      { type: 'agent', message: 'Risk Agent adjusted position sizing', agent: 'Risk-Guardian' },
      { type: 'data', message: 'Alternative data source integrated', agent: 'IoT Ingestor' },
      { type: 'security', message: 'Blockchain logger recorded 47 transactions', agent: 'Immutable Logger' },
      { type: 'execution', message: 'CPPN Evolver discovered new pattern', agent: 'Pattern Evolver' }
    ];

    return activities[Math.floor(Math.random() * activities.length)];
  };

  useEffect(() => {
    // Initialize with some activities
    const initialActivities = Array.from({ length: 5 }, (_, i) => ({
      id: i,
      ...generateActivity(),
      timestamp: Date.now() - i * 30000
    }));
    setActivities(initialActivities);

    // Add new activities every 3-8 seconds
    const interval = setInterval(() => {
      const newActivity = {
        id: Date.now(),
        ...generateActivity(),
        timestamp: Date.now()
      };

      setActivities(prev => [newActivity, ...prev.slice(0, 9)]); // Keep only 10 most recent
    }, Math.random() * 5000 + 3000);

    return () => clearInterval(interval);
  }, []);

  const getActivityStyle = (type) => {
    return activityTypes.find(t => t.type === type) || activityTypes[0];
  };

  const formatTime = (timestamp) => {
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  return (
    <div className="metric-card rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
        <Activity className="w-5 h-5 mr-2 text-green-400" />
        Live Activity Feed
      </h3>
      
      <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-hide">
        <AnimatePresence>
          {activities.map((activity) => {
            const style = getActivityStyle(activity.type);
            const Icon = style.icon;
            
            return (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 20, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className={`p-3 rounded-lg border ${style.bg} ${style.border}`}
              >
                <div className="flex items-start space-x-3">
                  <Icon className={`w-4 h-4 mt-0.5 ${style.color}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">{activity.message}</p>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-gray-400">{activity.agent}</span>
                      <span className="text-xs text-gray-500">{formatTime(activity.timestamp)}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ActivityFeed;
