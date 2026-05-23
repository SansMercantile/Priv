import { LucideIcon } from "lucide-react";

export interface SystemStats {
  totalProfit: number;
  dailyReturn: number;
  activeAgents: number;
  dataPoints: number;
  riskScore: number;
  executionSpeed: number;
}

export interface ChartDataPoint {
  time: number;
  value: number;
  volume: number;
  sentiment: number;
}

export interface Agent {
  id: number;
  name: string;
  type: string;
  status: "active" | "monitoring" | "offline";
  performance: number;
  reputation: number;
  iconName: string; // we'll resolve icons dynamically based on name
  color: "green" | "blue" | "purple" | "yellow" | "red";
  specialty: string;
  decisions: number;
  accuracy: number;
  lastAction: string;
}

export interface ArbLog {
  agent1: Agent | null;
  agent2: Agent | null;
  decision1: string;
  decision2: string;
  outcome: string;
}

export interface DataFeed {
  id: number;
  name: string;
  type: string;
  status: "active" | "monitoring" | "error";
  throughput: number;
  latency: number;
  iconName: string;
  color: "green" | "blue" | "purple" | "yellow" | "red";
  description: string;
}

export interface DataHistoryPoint {
  id: number;
  source: string;
  volume: number;
  timestamp: number;
  type: "price" | "news" | "sentiment" | "volume" | "order";
}

export interface SecurityBlock {
  zkpVerifications: number;
  blockchainLogs: number;
  encryptionStrength: number;
  threatLevel: "Low" | "Moderate" | "High";
  complianceScore: number;
}

export interface LogItem {
  id: number;
  type: string;
  message: string;
  severity: "info" | "success" | "warning" | "error";
  timestamp: number;
  iconName: string;
  color: string;
}

export interface ThreatPoint {
  id: number;
  x: number;
  y: number;
  severity: number;
  type: "intrusion" | "anomaly" | "compliance" | "fraud";
}

export interface AutomationStats {
  totalTasks: number;
  completedToday: number;
  successRate: number;
  avgExecutionTime: number;
  activeProcesses: number;
  savedHours: number;
  moduleCount: number;
}

export interface SimulationDetails {
  title: string;
  description: string;
}

export interface AutomationModule {
  id: number;
  name: string;
  description: string;
  status: "active" | "monitoring" | "error";
  tasksCompleted: number;
  efficiency: number;
  iconName: string;
  color: "green" | "blue" | "purple" | "yellow" | "red";
  features: string[];
}

export interface AutomationHistory {
  id: number;
  task: string;
  module: string;
  duration: number;
  status: "completed" | "failed";
  timestamp: number;
}

export interface ChatMessage {
  sender: "user" | "ai";
  text?: string;
  type?: "chart" | "standard";
  chartData?: Array<{ date: string; price: number }>;
  ticker?: string;
}

export interface StockAlert {
  ticker: string;
  direction: "above" | "below";
  price: number;
}

export interface TourStep {
  title: string;
  content: string;
  iconName: string;
  target: string | null;
}
