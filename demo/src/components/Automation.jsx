import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Zap, CheckCircle, Bot } from 'lucide-react';

import AutomationMetrics from './automation/AutomationMetrics';
import AutomationModules from './automation/AutomationModules';
import RecentTasks from './automation/RecentTasks';
import SystemHealth from './automation/SystemHealth';
import AutonomousCapabilities from './automation/AutonomousCapabilities';
import TaxAutomationPreview from './automation/TaxAutomationPreview';

const Automation = () => {
  const [automationMetricsData, setAutomationMetricsData] = useState({
    totalTasks: 15847,
    completedToday: 2847,
    successRate: 99.2,
    avgExecutionTime: 0.003,
    activeProcesses: 47,
    savedHours: 1247,
    moduleCount: 7 
  });

  const [automationModulesData, setAutomationModulesData] = useState([]);
  const [recentTasksData, setRecentTasksData] = useState([]);

  useEffect(() => {
    const modules = [
        { id: 1, name: 'Financial Automation', description: 'Automated accounts payable, FP&A, and reporting', status: 'active', tasksCompleted: 3847, efficiency: 98.7, icon: 'DollarSign', color: 'green', features: ['AP/AR Processing', 'FP&A Reports', 'Budget Analysis'] },
        { id: 2, name: 'Self-Healing System', description: 'Autonomous updates and issue resolution', status: 'active', tasksCompleted: 1247, efficiency: 99.8, icon: 'Wrench', color: 'blue', features: ['Auto Updates', 'Error Recovery', 'Health Monitoring'] },
        { id: 3, name: 'AI Sandbox', description: 'Secure testing environment for new strategies', status: 'active', tasksCompleted: 892, efficiency: 96.3, icon: 'Bot', color: 'purple', features: ['Strategy Testing', 'Risk Simulation', 'Backtesting'] },
        { id: 4, name: 'Support AI', description: 'Intelligent user support and market insights', status: 'active', tasksCompleted: 2156, efficiency: 94.1, icon: 'Activity', color: 'yellow', features: ['Query Handling', 'User Guidance', 'Report Generation'] },
        { id: 5, name: 'Document Processing', description: 'Automated document generation and compliance', status: 'monitoring', tasksCompleted: 634, efficiency: 97.5, icon: 'FileText', color: 'red', features: ['Contract Analysis', 'Compliance Docs', 'Data Extraction'] },
        { id: 6, name: 'System Orchestration', description: 'Coordinated automation across all modules', status: 'active', tasksCompleted: 1589, efficiency: 99.1, icon: 'Settings', color: 'green', features: ['Task Scheduling', 'Resource Management', 'Load Balancing'] },
        { id: 7, name: 'Tax Compliance (SARS & GRA)', description: 'Automated tax reporting for South Africa & Ghana', status: 'active', tasksCompleted: 451, efficiency: 99.5, icon: 'Landmark', color: 'blue', features: ['SARS eFiling', 'GRA Reporting', 'Compliance Checks'] },
    ];
    setAutomationModulesData(modules);

    const generateRecentTasks = () => {
      const taskTypes = [
        'Financial report generated', 'System update deployed', 'Strategy backtested', 'User query resolved', 'Compliance check completed', 'Performance optimization applied', 'Risk assessment updated', 'Market analysis completed', 'SARS tax report submitted'
      ];
      return Array.from({ length: 10 }, (_, i) => ({
        id: i,
        task: taskTypes[Math.floor(Math.random() * taskTypes.length)],
        module: modules[Math.floor(Math.random() * modules.length)].name,
        duration: Math.random() * 5 + 0.1,
        status: Math.random() > 0.1 ? 'completed' : 'failed',
        timestamp: Date.now() - i * 30000
      }));
    };
    setRecentTasksData(generateRecentTasks());

    const interval = setInterval(() => {
      setAutomationMetricsData(prev => ({
        ...prev,
        totalTasks: prev.totalTasks + Math.floor(Math.random() * 10 + 5),
        completedToday: prev.completedToday + Math.floor(Math.random() * 5 + 1),
        successRate: Math.max(95, Math.min(100, prev.successRate + (Math.random() - 0.5) * 1)),
        avgExecutionTime: Math.max(0.001, prev.avgExecutionTime + (Math.random() - 0.5) * 0.001),
        activeProcesses: Math.max(30, Math.min(60, prev.activeProcesses + Math.floor((Math.random() - 0.5) * 5))),
        savedHours: prev.savedHours + Math.floor(Math.random() * 3 + 1)
      }));
      setAutomationModulesData(prev => prev.map(module => ({
        ...module,
        tasksCompleted: module.tasksCompleted + Math.floor(Math.random() * 5 + 1),
        efficiency: Math.max(90, Math.min(100, module.efficiency + (Math.random() - 0.5) * 2))
      })));
      setRecentTasksData(generateRecentTasks());
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Automation & True Autonomy</h1>
          <p className="text-gray-400 mt-1">Full autonomous operation with minimal human intervention</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 rounded-lg border border-green-500/30">
            <Zap className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-medium">{automationMetricsData.activeProcesses} Active</span>
          </div>
          <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <CheckCircle className="w-5 h-5 text-blue-400" />
            <span className="text-blue-400 font-medium">{automationMetricsData.successRate.toFixed(1)}% Success</span>
          </div>
        </div>
      </div>

      <AutomationMetrics metrics={automationMetricsData} />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <AutomationModules modules={automationModulesData} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentTasks tasks={recentTasksData} />
        <SystemHealth />
      </div>

      <AutonomousCapabilities />
      <TaxAutomationPreview />
    </div>
  );
};

export default Automation;
