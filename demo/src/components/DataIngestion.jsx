import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Database, Globe, Rss, Wifi, BarChart3, Activity, TrendingUp, Zap } from 'lucide-react';
import { toast } from './ui/use-toast';

const DataIngestion = () => {
  const [dataSources, setDataSources] = useState([]);
  const [dataFlow, setDataFlow] = useState([]);
  const [totalDataPoints, setTotalDataPoints] = useState(2847392);

  useEffect(() => {
    const sources = [
      {
        id: 1,
        name: 'Market Data Feeds',
        type: 'WebSocket',
        status: 'active',
        throughput: 15420,
        latency: 0.003,
        icon: BarChart3,
        color: 'green',
        description: 'Real-time market prices and order book data'
      },
      {
        id: 2,
        name: 'News APIs',
        type: 'REST',
        status: 'active',
        throughput: 847,
        latency: 0.12,
        icon: Globe,
        color: 'blue',
        description: 'Global financial news and economic events'
      },
      {
        id: 3,
        name: 'Social Media',
        type: 'Streaming',
        status: 'active',
        throughput: 3241,
        latency: 0.08,
        icon: Rss,
        color: 'purple',
        description: 'Twitter, Reddit, and financial forums'
      },
      {
        id: 4,
        name: 'Economic Calendar',
        type: 'Scheduled',
        status: 'active',
        throughput: 156,
        latency: 0.05,
        icon: Activity,
        color: 'yellow',
        description: 'Central bank announcements and economic indicators'
      },
      {
        id: 5,
        name: 'IoT Sensors',
        type: 'MQTT',
        status: 'monitoring',
        throughput: 2847,
        latency: 0.15,
        icon: Wifi,
        color: 'red',
        description: 'Alternative data from IoT devices and sensors'
      },
      {
        id: 6,
        name: 'Blockchain Data',
        type: 'WebSocket',
        status: 'active',
        throughput: 1923,
        latency: 0.07,
        icon: Zap,
        color: 'green',
        description: 'On-chain transactions and DeFi protocols'
      }
    ];

    setDataSources(sources);

    // Generate data flow visualization
    const generateDataFlow = () => {
      return Array.from({ length: 20 }, (_, i) => ({
        id: i,
        source: sources[Math.floor(Math.random() * sources.length)].name,
        volume: Math.random() * 1000 + 100,
        timestamp: Date.now() - i * 1000,
        type: ['price', 'news', 'sentiment', 'volume', 'order'][Math.floor(Math.random() * 5)]
      }));
    };

    setDataFlow(generateDataFlow());

    // Update metrics periodically
    const interval = setInterval(() => {
      setDataSources(prev => prev.map(source => ({
        ...source,
        throughput: Math.max(0, source.throughput + (Math.random() - 0.5) * 200),
        latency: Math.max(0.001, source.latency + (Math.random() - 0.5) * 0.01)
      })));

      setTotalDataPoints(prev => prev + Math.floor(Math.random() * 1000 + 500));
      setDataFlow(generateDataFlow());
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const handleSourceClick = (source) => {
    toast({
      title: `📊 ${source.name} Details`,
      description: "This feature isn't implemented yet—but don't worry! You can request it in your next prompt! 🚀"
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'monitoring': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'error': return 'text-red-400 bg-red-500/20 border-red-500/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/30';
    }
  };

  const getColorClasses = (color) => {
    const colors = {
      green: 'border-green-500/20 sans-glow',
      blue: 'border-blue-500/20 sans-glow-blue',
      purple: 'border-purple-500/20',
      yellow: 'border-yellow-500/20',
      red: 'border-red-500/20'
    };
    return colors[color] || colors.green;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Data Ingestion & Analysis</h1>
          <p className="text-gray-400 mt-1">Multi-source data processing and fusion</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30">
            <Database className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-medium">{totalDataPoints.toLocaleString()} Points</span>
          </div>
          <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            <span className="text-blue-400 font-medium">+2.3K/min</span>
          </div>
        </div>
      </div>

      {/* Data Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {dataSources.map((source) => {
          const Icon = source.icon;
          
          return (
            <motion.div
              key={source.id}
              className={`metric-card rounded-xl p-6 cursor-pointer ${getColorClasses(source.color)}`}
              whileHover={{ scale: 1.02, y: -4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleSourceClick(source)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: source.id * 0.1 }}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg bg-${source.color}-500/20`}>
                    <Icon className={`w-5 h-5 text-${source.color}-400`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{source.name}</h3>
                    <p className="text-xs text-gray-400">{source.type}</p>
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(source.status)}`}>
                  {source.status}
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm text-gray-400">{source.description}</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-gray-400">Throughput</div>
                    <div className="text-lg font-bold text-white">{source.throughput.toFixed(0)}</div>
                    <div className="text-xs text-gray-500">msgs/sec</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-400">Latency</div>
                    <div className="text-lg font-bold text-white">{source.latency.toFixed(3)}s</div>
                    <div className="text-xs text-gray-500">avg</div>
                  </div>
                </div>

                <div className="pt-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Health</span>
                    <span className={`text-${source.color}-400`}>
                      {source.status === 'active' ? '100%' : '85%'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`bg-gradient-to-r from-${source.color}-500 to-${source.color}-400 h-2 rounded-full`}
                      style={{ width: source.status === 'active' ? '100%' : '85%' }}
                    ></div>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Data Flow Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          className="metric-card rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-green-400" />
            Real-time Data Flow
          </h3>
          
          <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-hide">
            {dataFlow.map((flow) => (
              <motion.div
                key={flow.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-center justify-between p-3 bg-black/30 rounded-lg border border-gray-700"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <div>
                    <div className="text-sm text-white">{flow.source}</div>
                    <div className="text-xs text-gray-400">{flow.type} data</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-green-400">{flow.volume.toFixed(0)}</div>
                  <div className="text-xs text-gray-500">msgs</div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Data Processing Pipeline */}
        <motion.div
          className="metric-card rounded-xl p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-400" />
            Processing Pipeline
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
                <span className="text-white">Data Ingestion</span>
              </div>
              <span className="text-blue-400 text-sm">24.7K/sec</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
                <span className="text-white">Data Cleaning</span>
              </div>
              <span className="text-purple-400 text-sm">22.1K/sec</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg border border-green-500/20">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <span className="text-white">Feature Extraction</span>
              </div>
              <span className="text-green-400 text-sm">19.8K/sec</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                <span className="text-white">Data Fusion</span>
              </div>
              <span className="text-yellow-400 text-sm">18.3K/sec</span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg border border-red-500/20">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                <span className="text-white">AI Processing</span>
              </div>
              <span className="text-red-400 text-sm">16.9K/sec</span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Processing Efficiency</span>
              <span className="text-green-400">94.2%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full w-[94%]"></div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Data Quality Metrics */}
      <motion.div
        className="metric-card rounded-xl p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
      >
        <h3 className="text-lg font-semibold text-white mb-4">Data Quality Metrics</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400 mb-2">99.7%</div>
            <div className="text-sm text-gray-400">Data Accuracy</div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full w-[99.7%]"></div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400 mb-2">98.3%</div>
            <div className="text-sm text-gray-400">Completeness</div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full w-[98.3%]"></div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400 mb-2">96.8%</div>
            <div className="text-sm text-gray-400">Consistency</div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full w-[96.8%]"></div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-400 mb-2">0.003s</div>
            <div className="text-sm text-gray-400">Avg Latency</div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full w-[95%]"></div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default DataIngestion;
