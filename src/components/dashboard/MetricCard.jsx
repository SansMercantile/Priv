import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const MetricCard = ({ title, value, change, icon: Icon, trend, color = 'green', onClick }) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-400" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getColorClasses = () => {
    const colors = {
      green: 'border-green-500/20 sans-glow',
      blue: 'border-blue-500/20 sans-glow-blue',
      purple: 'border-purple-500/20',
      yellow: 'border-yellow-500/20',
      red: 'border-red-500/20'
    };
    return colors[color] || colors.green;
  };

  const isClickable = !!onClick;

  return (
    <motion.div
      className={`metric-card rounded-xl p-4 ${getColorClasses()} ${isClickable ? 'cursor-pointer' : ''}`}
      whileHover={{ scale: isClickable ? 1.05 : 1.02 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-5 h-5 text-${color}-400`} />
        {getTrendIcon()}
      </div>
      
      <div className="space-y-1">
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{title}</p>
        <p className="text-xs text-gray-500">{change}</p>
      </div>
    </motion.div>
  );
};

export default MetricCard;
