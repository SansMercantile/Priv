import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

// --- Restored Original Imports ---
import apiClient from '../api/apiClient'; 
import Sidebar from '../components/Sidebar';
import ProfileDropdown from '../components/ProfileDropdown';
import UnifiedAssistant from '../ui/UnifiedAssistant';
import TreasuryDashboard from '../components/TreasuryDashboard';
import SystemIntegrityDashboard from '../components/SystemIntegrityDashboard';
import ConnectionsPage from './ConnectionsPage';
import MultiAgent from '../components/MultiAgent';
import NewsPage from './NewsPage';
import InsightsPage from './InsightsPage';
import VisionPage from './VisionPage';
import AudioPage from './AudioPage';
import AlertsPage from './AlertsPage';
import BrokerPage from './BrokerPage';
import TradeExecutorPage from './TradeExecutorPage';
import WalletPage from './WalletPage';
import FundingPage from './FundingPage';
import VenturesPage from './VenturesPage';
import LegalPage from './LegalPage';
import TaxPage from './TaxPage';
import ProfilePage from './ProfilePage';
import { MessageSquare } from '../components/icons/Icons';

// --- MODIFIED: Redefined PrivAvatar to fix the icon styling ---
// This new component ensures the image is circular and fits the container.
const PrivAvatar = ({ className }) => (
    <img 
        src="/priv-avatar.svg" // Using a placeholder that matches the style of your avatar
        alt="Priv AI Assistant"
        // The key fix is adding rounded-full and object-cover to the image itself
        className={cn("rounded-full object-cover", className)}
        onError={(e) => { e.target.onerror = null; e.target.src = 'https://placehold.co/100x100/1f0000/f0f0f0?text=P'; }} // Fallback in case image fails to load
    />
);


const cn = (...classes) => classes.filter(Boolean).join(' ');

// --- Positions Table Component (Restyled for light theme) ---
const PositionsTable = () => {
    const [positions, setPositions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchPositions = async () => {
            setIsLoading(true);
            try {
                await new Promise(resolve => setTimeout(resolve, 1500));
                const mockData = [
                    { instrument: 'S&P 500 CFD', type: 'Buy', quantity: 1225, entryPrice: 4100.50, currentPrice: 4150.20, profitLoss: 6570 },
                    { instrument: 'EUR/USD', type: 'Sell', quantity: 100000, entryPrice: 1.1050, currentPrice: 1.0950, profitLoss: 1000 },
                    { instrument: 'Gold CFD', type: 'Buy', quantity: 1980.30, entryPrice: 1960.10, currentPrice: 1960.10, profitLoss: -1410 },
                    { instrument: 'GBP/JPY', type: 'Sell', quantity: 50000, entryPrice: 156.75, currentPrice: 157.25, profitLoss: -250 },
                ];
                setPositions(mockData);
            } catch (error) {
                console.error("Failed to fetch positions:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchPositions();
    }, []);

    const TableRow = ({ position }) => (
        <tr className="border-b border-gray-200/80 hover:bg-gray-50/50 transition-colors duration-200">
            <td className="p-4 font-semibold text-gray-800">{position.instrument}</td>
            <td className={`p-4 font-bold ${position.type === 'Buy' ? 'text-green-600' : 'text-red-600'}`}>{position.type}</td>
            <td className="p-4 text-gray-700">{position.quantity.toLocaleString()}</td>
            <td className="p-4 text-gray-700">{position.entryPrice.toFixed(4)}</td>
            <td className="p-4 text-gray-700">{position.currentPrice.toFixed(4)}</td>
            <td className={`p-4 font-bold ${position.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {position.profitLoss >= 0 ? '+' : ''}{position.profitLoss.toLocaleString()}
            </td>
        </tr>
    );

    return (
        <div className="bg-white/50 backdrop-blur-md p-6 rounded-2xl shadow-lg border border-gray-200/50">
            <h3 className="text-xl font-bold mb-4 text-burgundy-black">Positions</h3>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b-2 border-gray-300/60 text-sm text-gray-500 uppercase">
                            <th className="p-4 font-semibold">Instrument</th>
                            <th className="p-4 font-semibold">Type</th>
                            <th className="p-4 font-semibold">Quantity</th>
                            <th className="p-4 font-semibold">Entry Price</th>
                            <th className="p-4 font-semibold">Current Price</th>
                            <th className="p-4 font-semibold">Profit/Loss</th>
                        </tr>
                    </thead>
                    <tbody>
                        {isLoading ? (
                            Array.from({ length: 4 }).map((_, i) => (
                                <tr key={i} className="border-b border-gray-200/80">
                                    <td colSpan="6" className="p-4">
                                        <div className="h-6 bg-gray-300/50 rounded animate-pulse"></div>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            positions.map((pos, index) => <TableRow key={index} position={pos} />)
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// --- ESG Score Chart Component ---
const EsgScoreChart = ({ score }) => {
    const dataPoints = [65, 68, 70, 69, 72, 71, 73, 75];
    
    const createSvgPath = (points) => {
        if (!points || points.length === 0) return "";
        const width = 100;
        const height = 30;
        const maxVal = Math.max(...points, 80);
        const minVal = Math.min(...points, 60);
        const range = maxVal - minVal || 1;

        const pathData = points.map((p, i) => {
            const x = (i / (points.length - 1)) * width;
            const y = height - ((p - minVal) / range) * height;
            return `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`;
        }).join(' ');
        
        return pathData;
    };

    const path = createSvgPath(dataPoints);

    return (
        <div className="h-full flex flex-col justify-between">
            <p className="text-4xl font-bold text-burgundy-black">{score}</p>
            <div className="h-8 w-full">
                <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="w-full h-full">
                    <path d={path} fill="none" stroke="#28A745" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </div>
        </div>
    );
};

// --- Main Dashboard View (MODIFIED) ---
const MainDashboardView = () => {
    const [metrics, setMetrics] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchMetrics = async () => {
            setIsLoading(true);
            try {
                await new Promise(resolve => setTimeout(resolve, 1000));
                // We only need these three metrics now
                setMetrics({ portfolioValue: 128760, signalConfidence: 98.7, esgScore: 75 });
            } catch (error) {
                console.error("Failed to fetch dashboard metrics:", error);
                setMetrics({ portfolioValue: 128760, signalConfidence: 98.7, esgScore: 75 });
            } finally {
                setIsLoading(false);
            }
        };
        fetchMetrics();
    }, []);

    const MetricCard = ({ title, children, className = "" }) => (
      <div className={cn("premium-glass-card p-4 text-center flex flex-col justify-center h-32", className)}>
          <h4 className="text-sm text-gray-500 font-semibold mb-2">{title}</h4>
          {isLoading ? (
            <div className="h-10 bg-gray-300/50 rounded animate-pulse w-3/4 mx-auto"></div>
           ) : children}
      </div>
    );

    // Helper function to determine the color for the confidence score
    const getConfidenceColor = (score) => {
        if (score >= 80) return 'text-green-600';
        if (score >= 60) return 'text-orange-500';
        return 'text-red-600';
    };

    return (
        <div className="p-6">
            {/* MODIFIED: Simplified grid with only 3 cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <MetricCard title="Portfolio Value">
                    <p className="text-4xl font-bold text-burgundy-black">${(metrics?.portfolioValue || 0).toLocaleString()}</p>
                </MetricCard>
                
                <MetricCard title="Predictive Signal Confidence">
                    <p className={cn("text-4xl font-bold", getConfidenceColor(metrics?.signalConfidence))}>
                        {metrics?.signalConfidence}<span className="text-xl ml-1 opacity-80">%</span>
                    </p>
                </MetricCard>

                <MetricCard title="ESG Score">
                    <EsgScoreChart score={metrics?.esgScore} />
                </MetricCard>
            </div>
            
            <PositionsTable />
        </div>
    );
};

// --- Main App Structure (Restored to original theme) ---

const PlaceholderPage = ({ title }) => (<div className="p-8"><h1 className="text-4xl font-serif text-burgundy-black mb-2">{title}</h1></div>);

export default function DashboardPage({ user, signOutUser }) {
  const [isSidebarMinimized, setIsSidebarMinimized] = useState(true);
  const [showPrivChat, setShowPrivChat] = useState(false);
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname.split('/').pop();
    if (!path || path === 'dashboard') return 'Dashboard';
    return path.charAt(0).toUpperCase() + path.slice(1).replace('-', ' ');
  };

  return (
    <div className="flex h-screen bg-silver font-sans">
      <Sidebar 
        isMinimized={isSidebarMinimized} 
        onToggle={() => setIsSidebarMinimized(p => !p)} 
      />
      <div className="flex-1 flex flex-col">
        <header className="flex justify-between items-center p-4 bg-silver flex-shrink-0 border-b border-border-color">
            <h1 className="text-2xl font-bold font-serif text-burgundy-black">{getPageTitle()}</h1>
            <ProfileDropdown user={user} signOutUser={signOutUser} />
        </header>
        <main className="flex-1 overflow-y-auto">
            <Routes>
                <Route path="/" element={<MainDashboardView />} />
                <Route path="/treasury" element={<TreasuryDashboard />} />
                <Route path="/integrity" element={<SystemIntegrityDashboard />} />
                <Route path="/multi-agent" element={<MultiAgent />} />
                <Route path="/news" element={<NewsPage />} />
                <Route path="/insights" element={<InsightsPage />} />
                <Route path="/analytics" element={<PlaceholderPage title="AI Analytics" />} />
                <Route path="/vision" element={<VisionPage />} />
                <Route path="/audio" element={<AudioPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/broker" element={<BrokerPage />} />
                <Route path="/trade-executor" element={<TradeExecutorPage />} />
                <Route path="/wallet" element={<WalletPage />} />
                <Route path="/funding" element={<FundingPage />} />
                <Route path="/ventures" element={<VenturesPage />} />
                <Route path="/legal" element={<LegalPage />} />
                <Route path="/tax" element={<TaxPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/risk" element={<PlaceholderPage title="Risk Analysis" />} />
                <Route path="/history" element={<PlaceholderPage title="Trade History" />} />
                <Route path="/connections" element={<ConnectionsPage />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </main>
      </div>
      {!showPrivChat && (
        <div id="privFabContainer" className="fixed bottom-6 right-6 z-50">
          <button onClick={() => setShowPrivChat(true)} className="bg-burgundy-black text-white w-16 h-16 rounded-full shadow-2xl flex items-center justify-center p-0 overflow-hidden">
              <PrivAvatar className="w-full h-full" />
          </button>
        </div>
      )}
    <UnifiedAssistant isVisible={showPrivChat} onClose={() => setShowPrivChat(false)} />
    </div>
  );
};
