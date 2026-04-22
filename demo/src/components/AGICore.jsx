import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Heart, Eye, Zap, Activity, TrendingUp } from 'lucide-react';
import { toast } from './ui/use-toast';

const AGICore = () => {
  const [empathyScore, setEmpathyScore] = useState(87.3);
  const [consciousnessLevel, setConsciousnessLevel] = useState(94.2);
  const [emotionalState, setEmotionalState] = useState('Optimistic');
  const [neuralActivity, setNeuralActivity] = useState([]);

  useEffect(() => {
    // Generate neural activity data
    const generateNeuralData = () => {
      return Array.from({ length: 100 }, (_, i) => ({
        x: i,
        y: Math.sin(i * 0.1) * 30 + 50 + Math.random() * 20,
        intensity: Math.random()
      }));
    };

    setNeuralActivity(generateNeuralData());

    // Update metrics periodically
    const interval = setInterval(() => {
      setEmpathyScore(prev => Math.max(0, Math.min(100, prev + (Math.random() - 0.5) * 5)));
      setConsciousnessLevel(prev => Math.max(0, Math.min(100, prev + (Math.random() - 0.5) * 3)));
      
      const emotions = ['Optimistic', 'Analytical', 'Cautious', 'Confident', 'Adaptive'];
      setEmotionalState(emotions[Math.floor(Math.random() * emotions.length)]);
      
      setNeuralActivity(generateNeuralData());
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleEmpathyEngineClick = () => {
    toast({
      title: "🧠 Empathy Engine Analysis",
      description: "This feature isn't implemented yet—but don't worry! You can request it in your next prompt! 🚀"
    });
  };

  const handleConsciousnessClick = () => {
    toast({
      title: "🌟 Unified Consciousness",
      description: "This feature isn't implemented yet—but don't worry! You can request it in your next prompt! 🚀"
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">AGI Core Intelligence</h1>
          <p className="text-gray-400 mt-1">Artificial General Intelligence with Emotional Layer</p>
        </div>
        <div className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 rounded-lg border border-purple-500/30">
          <Brain className="w-5 h-5 text-purple-400" />
          <span className="text-purple-400 font-medium">AGI Active</span>
        </div>
      </div>

      {/* Core Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          className="metric-card rounded-xl p-6 border-purple-500/20"
          whileHover={{ scale: 1.02 }}
          onClick={handleEmpathyEngineClick}
          style={{ cursor: 'pointer' }}
        >
          <div className="flex items-center justify-between mb-4">
            <Heart className="w-8 h-8 text-pink-400" />
            <div className="text-right">
              <div className="text-2xl font-bold text-white">{empathyScore.toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Empathy Score</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Market Psychology</span>
              <span className="text-pink-400">High</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-pink-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${empathyScore}%` }}
              ></div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="metric-card rounded-xl p-6 border-blue-500/20"
          whileHover={{ scale: 1.02 }}
          onClick={handleConsciousnessClick}
          style={{ cursor: 'pointer' }}
        >
          <div className="flex items-center justify-between mb-4">
            <Eye className="w-8 h-8 text-blue-400" />
            <div className="text-right">
              <div className="text-2xl font-bold text-white">{consciousnessLevel.toFixed(1)}%</div>
              <div className="text-sm text-gray-400">Consciousness</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Unified State</span>
              <span className="text-blue-400">Optimal</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${consciousnessLevel}%` }}
              ></div>
            </div>
          </div>
        </motion.div>

        <motion.div
          className="metric-card rounded-xl p-6 border-green-500/20"
          whileHover={{ scale: 1.02 }}
        >
          <div className="flex items-center justify-between mb-4">
            <Zap className="w-8 h-8 text-green-400" />
            <div className="text-right">
              <div className="text-2xl font-bold text-white">{emotionalState}</div>
              <div className="text-sm text-gray-400">Emotional State</div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Market Sentiment</span>
              <span className="text-green-400">Positive</span>
            </div>
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex-1 h-2 bg-gray-700 rounded-full">
                  <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"></div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Neural Activity Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="metric-card rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-purple-400" />
            Neural Activity Map
          </h3>
          
          <div className="relative h-64 bg-black/50 rounded-lg overflow-hidden">
            <svg className="w-full h-full">
              {neuralActivity.map((point, i) => (
                <circle
                  key={i}
                  cx={`${(point.x / 100) * 100}%`}
                  cy={`${(point.y / 100) * 100}%`}
                  r={point.intensity * 3 + 1}
                  fill={`rgba(147, 51, 234, ${point.intensity})`}
                  className="animate-pulse"
                />
              ))}
              
              {/* Neural connections */}
              {neuralActivity.slice(0, 20).map((point, i) => {
                const nextPoint = neuralActivity[i + 1];
                if (!nextPoint) return null;
                
                return (
                  <line
                    key={`line-${i}`}
                    x1={`${(point.x / 100) * 100}%`}
                    y1={`${(point.y / 100) * 100}%`}
                    x2={`${(nextPoint.x / 100) * 100}%`}
                    y2={`${(nextPoint.y / 100) * 100}%`}
                    stroke="rgba(147, 51, 234, 0.3)"
                    strokeWidth="1"
                  />
                );
              })}
            </svg>
            
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            <div className="absolute bottom-4 left-4 text-white">
              <div className="text-sm font-medium">Active Neurons: {neuralActivity.length}</div>
              <div className="text-xs text-gray-400">Real-time processing</div>
            </div>
          </div>
        </motion.div>

        {/* AGI Capabilities */}
        <motion.div
          className="metric-card rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
            AGI Capabilities
          </h3>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Strategic Planning</span>
                <span className="text-green-400">96%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full w-[96%]"></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Pattern Recognition</span>
                <span className="text-blue-400">94%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full w-[94%]"></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Emotional Intelligence</span>
                <span className="text-purple-400">91%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full w-[91%]"></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Risk Assessment</span>
                <span className="text-yellow-400">89%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full w-[89%]"></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-400">Adaptive Learning</span>
                <span className="text-red-400">97%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-red-500 to-pink-500 h-2 rounded-full w-[97%]"></div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Recent AGI Decisions */}
      <motion.div
        className="metric-card rounded-xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4">Recent AGI Decisions</h3>
        
        <div className="space-y-4">
          <div className="flex items-start space-x-4 p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
            <Brain className="w-5 h-5 text-purple-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-white font-medium">Strategic Portfolio Rebalancing</div>
              <div className="text-gray-400 text-sm mt-1">
                AGI Core detected market regime change and initiated 15% portfolio reallocation to defensive assets
              </div>
              <div className="text-xs text-gray-500 mt-2">Confidence: 94% • Impact: High • 3 minutes ago</div>
            </div>
          </div>
          
          <div className="flex items-start space-x-4 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
            <Heart className="w-5 h-5 text-blue-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-white font-medium">Emotional Sentiment Override</div>
              <div className="text-gray-400 text-sm mt-1">
                Empathy Engine detected excessive market fear, overriding quantitative signals for contrarian positioning
              </div>
              <div className="text-xs text-gray-500 mt-2">Confidence: 87% • Impact: Medium • 8 minutes ago</div>
            </div>
          </div>
          
          <div className="flex items-start space-x-4 p-4 bg-green-500/10 rounded-lg border border-green-500/20">
            <Eye className="w-5 h-5 text-green-400 mt-0.5" />
            <div className="flex-1">
              <div className="text-white font-medium">Multi-Timeframe Analysis</div>
              <div className="text-gray-400 text-sm mt-1">
                Unified Consciousness synthesized signals across 12 timeframes, identifying optimal entry point
              </div>
              <div className="text-xs text-gray-500 mt-2">Confidence: 96% • Impact: High • 12 minutes ago</div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AGICore;
