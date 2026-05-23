import React from 'react';
import { BarChart4 } from 'lucide-react';

// A reusable Card component local to this dashboard
const Card = ({ title, children }) => (
    <div className="bg-white p-4 rounded-lg shadow-custom-light border border-border-color h-full flex flex-col">
        {title && <h3 className="font-bold text-text-primary font-serif text-lg mb-3">{title}</h3>}
        <div className="flex-grow">{children}</div>
    </div>
);

/**
 * TreasuryDashboard Component
 * Displays a comprehensive overview of treasury, agents, governance, and infrastructure.
 */
const TreasuryDashboard = () => {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
            {/* Column 1 */}
            <div className="flex flex-col gap-6">
                <Card title="StrategicAdvisor">
                    <div className="h-32 bg-gray-200 rounded flex items-center justify-center">
                        <BarChart4 className="w-10 h-10 text-gray-400"/>
                    </div>
                    <div className="flex justify-end mt-2">
                        <button className="text-xs bg-input-bg px-2 py-1 rounded hover:bg-gray-300">PAUSE TRADING</button>
                    </div>
                    <div className="text-xs mt-2 space-y-1">
                        <p>Risk Mode: <span className="font-semibold">Balanced</span></p>
                        <p>Bought X <span className="text-text-secondary">23m ago</span></p>
                        <p>Sold Y <span className="text-text-secondary">9m ago</span></p>
                    </div>
                </Card>
                <Card title="Synthetic Sandbox">
                    <div className="h-24 bg-gray-200 rounded flex items-center justify-center">
                        <p className="text-text-secondary text-sm">Strategy Replay</p>
                    </div>
                </Card>
                <Card title="Tax & Treasury">
                    <p className="text-text-secondary text-sm p-2">SARS-ready form viewer and tax buffer tracker will be here.</p>
                </Card>
            </div>

            {/* Column 2 */}
            <div className="flex flex-col gap-6">
                <Card title="Agent Constellation">
                    <div className="grid grid-cols-2 gap-2 text-center text-xs">
                        <div className="bg-gray-200 p-2 rounded font-semibold">Role</div>
                        <div className="bg-gray-200 p-2 rounded font-semibold">Reputation</div>
                        <div className="bg-gray-100 p-2 rounded">Expert</div>
                        <div className="bg-gray-100 p-2 rounded">0.95</div>
                        <div className="bg-gray-100 p-2 rounded">Biput T</div>
                        <div className="bg-gray-100 p-2 rounded">0.92</div>
                        <div className="bg-gray-100 p-2 rounded">Biput Z</div>
                        <div className="bg-gray-100 p-2 rounded">0.88</div>
                    </div>
                </Card>
                <Card title="ZK Audit Trail">
                    <p className="text-text-secondary text-sm p-2">ActionToken ledger with ZKVerifier status will be displayed here.</p>
                </Card>
                <Card title="Infrastructure Ops">
                    <p className="text-text-secondary text-sm p-2">Container, Broker, Messaging, and Storage status.</p>
                </Card>
            </div>

            {/* Column 3 */}
            <div className="flex flex-col gap-6">
                <Card title="Governance">
                    <p className="text-text-secondary text-sm p-2">Governance chat log and manual override history.</p>
                </Card>
                <Card title="Sovereign Identity">
                    <p className="text-text-secondary text-sm p-2">Operating mandate, card vault, and override permissions.</p>
                </Card>
            </div>
        </div>
    );
};

export default TreasuryDashboard;
