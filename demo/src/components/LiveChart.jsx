import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';

const LiveChart = ({ data }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const { width, height } = rect;

    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(0, 255, 136, 0.3)');
    gradient.addColorStop(1, 'rgba(0, 255, 136, 0)');

    const values = data.map(d => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;

    // Draw area chart
    ctx.beginPath();
    ctx.moveTo(0, height);
    data.forEach((point, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((point.value - minValue) / range) * (height - 20) - 10;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    data.forEach((point, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((point.value - minValue) / range) * (height - 20) - 10;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw sentiment bar at the bottom
    data.forEach((point, index) => {
      const x = (index / (data.length - 1)) * width;
      const barWidth = width / (data.length - 1);
      const sentimentColor = `rgba(${255 * (1 - point.sentiment)}, ${255 * point.sentiment}, 0, 0.6)`;
      ctx.fillStyle = sentimentColor;
      ctx.fillRect(x, height - 5, barWidth, 5);
    });

  }, [data]);

  const latestData = data[data.length - 1] || {};
  const sentimentLabel = latestData.sentiment > 0.7 ? "Bullish" : latestData.sentiment < 0.3 ? "Bearish" : "Neutral";
  const sentimentColor = latestData.sentiment > 0.7 ? "text-green-400" : latestData.sentiment < 0.3 ? "text-red-400" : "text-yellow-400";


  return (
    <motion.div
      className="metric-card rounded-xl p-6"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-green-400" />
          Live Performance & Sentiment
        </h3>
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          <span>Real-time P&L</span>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      </div>
      
      <div className="relative">
        <canvas
          ref={canvasRef}
          className="w-full h-64 rounded-lg"
        />
        
        <div className="absolute top-4 left-4 space-y-1">
          <div className="text-2xl font-bold text-green-400">
            ${latestData.value ? latestData.value.toFixed(2) : '0.00'}
          </div>
          <div className="text-sm text-gray-400">Current Value</div>
        </div>
        
        <div className="absolute top-4 right-4 space-y-1 text-right">
          <div className={`text-lg font-semibold ${sentimentColor}`}>{sentimentLabel}</div>
          <div className="text-sm text-gray-400">Market Sentiment</div>
        </div>
        
        <div className="absolute bottom-4 right-4 space-y-1 text-right text-xs text-gray-500 flex items-center gap-2">
            <div className="w-3 h-1.5 bg-red-500 rounded-sm"></div>
            <span>Bearish</span>
            <div className="w-3 h-1.5 bg-yellow-500 rounded-sm"></div>
            <span>Neutral</span>
            <div className="w-3 h-1.5 bg-green-500 rounded-sm"></div>
            <span>Bullish</span>
        </div>
      </div>
    </motion.div>
  );
};

export default LiveChart;
