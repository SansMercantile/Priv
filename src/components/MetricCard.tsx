import React from "react";
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "stable";
  color?: "green" | "blue" | "purple" | "yellow" | "red";
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  trend = "stable",
  color = "green",
  onClick
}) => {
  // Styles based on color choices - updated for Sophisticated Dark aesthetic
  const colorMap = {
    green: {
      border: "border-white/10 hover:border-white/25",
      text: "text-white",
      bg: "bg-white/5",
    },
    blue: {
      border: "border-white/10 hover:border-white/25",
      text: "text-white",
      bg: "bg-white/5",
    },
    purple: {
      border: "border-white/10 hover:border-white/25",
      text: "text-white",
      bg: "bg-white/5",
    },
    yellow: {
      border: "border-white/10 hover:border-white/25",
      text: "text-white/90",
      bg: "bg-white/5",
    },
    red: {
      border: "border-white/10 hover:border-white/25",
      text: "text-white",
      bg: "bg-white/5",
    }
  };

  const selectedColor = colorMap[color] || colorMap.green;

  return (
    <div
      onClick={onClick}
      className={`metric-card rounded-xl p-5 ${selectedColor.border} ${
        onClick ? "cursor-pointer" : ""
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        {/* Metric Icon */}
        <div className={`p-2 rounded-lg ${selectedColor.bg}`}>
          <Icon className={`w-5 h-5 ${selectedColor.text}`} />
        </div>

        {/* Trend Indicator */}
        <div className="flex items-center space-x-1 font-mono text-xs">
          {trend === "up" && (
            <span className="flex items-center text-green-400">
              <TrendingUp className="w-3.5 h-3.5 mr-1" />
            </span>
          )}
          {trend === "down" && (
            <span className="flex items-center text-red-400">
              <TrendingDown className="w-3.5 h-3.5 mr-1" />
            </span>
          )}
          {trend === "stable" && (
            <span className="flex items-center text-gray-400">
              <Minus className="w-3.5 h-3.5 mr-1" />
            </span>
          )}
        </div>
      </div>

      <div>
        <h4 className="text-xs font-mono text-gray-400 uppercase tracking-widest leading-none mb-2">
          {title}
        </h4>
        <div className="text-2xl font-light tracking-tight text-white mb-1">
          {value}
        </div>
        <div className="flex items-center text-[10px] font-mono text-gray-500">
          <span className={`${trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-400"}`}>
            {change}
          </span>
        </div>
      </div>
    </div>
  );
};
