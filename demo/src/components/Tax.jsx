import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, Landmark, Users, Gamepad2, Brain, BarChart, TrendingUp, ShieldCheck } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from './ui/use-toast';

const MetricTile = ({ icon: Icon, label, value, color }) => (
    <motion.div 
        className={`metric-card rounded-xl p-4 border-${color}-500/20`}
        whileHover={{scale: 1.05}}
    >
        <div className="flex items-center space-x-3">
            <Icon className={`w-6 h-6 text-${color}-400`} />
            <div>
                <p className="text-xs text-gray-400">{label}</p>
                <p className="text-lg font-bold text-white">{value}</p>
            </div>
        </div>
    </motion.div>
);

const Tax = () => {
    const [revenuePrediction, setRevenuePrediction] = useState(14.7);
    const [complianceGaps, setComplianceGaps] = useState(12843);

    useEffect(() => {
        const interval = setInterval(() => {
            setRevenuePrediction(prev => prev + (Math.random() - 0.5) * 0.2);
            setComplianceGaps(prev => prev + Math.floor((Math.random() - 0.4) * 100));
        }, 3000);
        return () => clearInterval(interval);
    }, []);

    const showToast = (title) => {
        toast({
            title: `🚀 ${title}`,
            description: "This feature isn't implemented yet—but don't worry! You can request it in your next prompt! 🚀"
        });
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold gradient-text">Tax Intelligence Engine</h1>
                    <p className="text-gray-400 mt-1">Revolutionizing Public Revenue for Governments (GRA & SARS)</p>
                </div>
                <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-lg border border-blue-500/30">
                    <Landmark className="w-5 h-5 text-blue-400" />
                    <span className="text-blue-400 font-medium">Gov-Tech Module Active</span>
                </div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
            >
                <MetricTile icon={BarChart} label="Predicted Revenue (billions)" value={`$${revenuePrediction.toFixed(2)}`} color="green" />
                <MetricTile icon={TrendingUp} label="Identified Compliance Gaps" value={complianceGaps.toLocaleString()} color="yellow" />
                <MetricTile icon={ShieldCheck} label="Policy Simulation Accuracy" value="97.3%" color="blue" />
                <MetricTile icon={Users} label="Citizen Engagement Score" value="88.9%" color="purple" />
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Pillar 1 */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="space-y-6"
                >
                    <h2 className="text-2xl font-semibold text-white flex items-center"><Brain className="w-8 h-8 mr-3 text-green-400" />The Tax Intelligence Engine</h2>
                    <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-green-400">Predict Tax Revenue</h3>
                        <p className="text-gray-400 text-sm">Deploying Priv Sentiment and Economic Agents to analyze vast data sources, forecasting revenue from informal sectors with unprecedented accuracy.</p>
                        <Button variant="outline" className="border-green-500 text-green-400 hover:bg-green-500/10" onClick={() => showToast("Revenue Prediction Details")}>View Forecast Models</Button>
                    </div>
                    <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-yellow-400">Identify & Bridge Compliance Gaps</h3>
                        <p className="text-gray-400 text-sm">The Priv Tax Agent, powered by our Neuro-symbolic Engine, identifies non-compliance patterns and recommends targeted interventions, from educational campaigns to focused outreach programs.</p>
                        <Button variant="outline" className="border-yellow-500 text-yellow-400 hover:bg-yellow-500/10" onClick={() => showToast("Compliance Gap Analysis")}>Explore Compliance Map</Button>
                    </div>
                     <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-blue-400">Simulate Policy Outcomes</h3>
                        <p className="text-gray-400 text-sm">Utilizing the CPPN Evolver and Subatomic Analysis, we model the potential impact of new tax policies, ensuring data-driven decisions and minimizing unintended consequences.</p>
                        <Button variant="outline" className="border-blue-500 text-blue-400 hover:bg-blue-500/10" onClick={() => showToast("Policy Simulation Sandbox")}>Run a Simulation</Button>
                    </div>
                </motion.div>

                {/* Pillar 2 */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="space-y-6"
                >
                    <h2 className="text-2xl font-semibold text-white flex items-center"><Users className="w-8 h-8 mr-3 text-purple-400" />Citizen-Centric Compliance</h2>
                    <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-purple-400">Adaptive Tax Education Tools</h3>
                        <p className="text-gray-400 text-sm">Our Emotion Driver and Empathy Engine create adaptive tutorials that gauge user sentiment, ensuring every citizen feels understood and supported through their tax journey.</p>
                        <Button variant="outline" className="border-purple-500 text-purple-400 hover:bg-purple-500/10" onClick={() => showToast("Adaptive Education Demo")}>Try Interactive Guide</Button>
                    </div>
                    <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-teal-400">AI-Powered Support Agents</h3>
                        <p className="text-gray-400 text-sm">Deploying 24/7 AI support via platforms like WhatsApp to guide users through registration, filing, and payments, dramatically reducing friction.</p>
                        <Button variant="outline" className="border-teal-500 text-teal-400 hover:bg-teal-500/10" onClick={() => showToast("AI Support Chat")}>Chat with Support Agent</Button>
                    </div>
                     <div className="metric-card rounded-xl p-6 space-y-4">
                        <h3 className="font-semibold text-lg text-pink-400">Gamified Incentives & Reputation</h3>
                        <p className="text-gray-400 text-sm">Our Agent Reputation Ledger tracks a gamified incentive system. Consistent, timely compliance earns citizens rewards like tax credits and public recognition, making tax payment an engaging experience.</p>
                        <Button variant="outline" className="border-pink-500 text-pink-400 hover:bg-pink-500/10" onClick={() => showToast("Gamified Ledger")}>View Reputation Rankings</Button>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default Tax;
