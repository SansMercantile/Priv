// src/components/Sidebar.jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Brain, Users, Database, Shield, Zap, FileText, BarChart4, TrendingDown, History, PlugZap, Newspaper, Power, Globe, AlertTriangle } from 'lucide-react';

const cn = (...classes) => classes.filter(Boolean).join(' ');

// Sans Mercantile Logo Icon Component
const LogoIcon = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" className={className}>
        <defs>
            <linearGradient id="orangeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{stopColor:'#FF6B35', stopOpacity:1}} />
                <stop offset="100%" style={{stopColor:'#FF8C42', stopOpacity:1}} />
            </linearGradient>
            <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>
        <path d="M 30 25 Q 20 25 20 35 Q 20 45 30 45 L 50 45 Q 60 45 60 55 Q 60 65 50 65 L 30 65 Q 20 65 20 75" 
            stroke="url(#orangeGlow)" 
            strokeWidth="6" 
            fill="none" 
            strokeLinecap="round"
            filter="url(#glow)"/>
        <path d="M 65 75 L 65 25 L 75 40 L 85 25 L 85 75" 
            stroke="#FFFFFF" 
            strokeWidth="6" 
            fill="none" 
            strokeLinecap="round"
            filter="url(#glow)"
            style={{filter: 'drop-shadow(0 0 8px rgba(255, 255, 255, 0.8))'}}/>
    </svg>
);

export default function Sidebar({ isMinimized, onToggle, demoMode, onDemoModeToggle, isDemoLocked = false }) {
    const location = useLocation();

    // Main navigation items (top-level)
    const navItems = [
        { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/dashboard/agi-core', label: 'AGI Core', icon: Brain },
        { path: '/dashboard/multi-agent', label: 'Multi-Agent', icon: Users },
        { path: '/dashboard/data-ingestion', label: 'Data Ingestion', icon: Database },
        { path: '/dashboard/security', label: 'Security', icon: Shield },
        { path: '/dashboard/automation', label: 'Automation', icon: Zap },
        { path: '/dashboard/tax', label: 'Tax Intelligence', icon: FileText },
    ];

    // Systems section (collapsible)
    const systemsItems = [
        { path: '/dashboard/news', label: 'News', icon: Newspaper },
        { path: '/dashboard/analytics', label: 'Analytics', icon: BarChart4 },
        { path: '/dashboard/insights', label: 'Market Insights', icon: TrendingDown },
        { path: '/dashboard/history', label: 'History', icon: History },
        { path: '/dashboard/vision', label: 'Vision', icon: Globe },
        { path: '/dashboard/audio', label: 'Audio', icon: Users },
        { path: '/dashboard/alerts', label: 'Alerts', icon: AlertTriangle },
        { path: '/dashboard/connections', label: 'Connections', icon: PlugZap },
        { path: '/dashboard/broker', label: 'Broker Interface', icon: Zap },
        { path: '/dashboard/trade-executor', label: 'Trade Executor', icon: Zap },
        { path: '/dashboard/wallet', label: 'Wallet Vault', icon: Database },
        { path: '/dashboard/funding', label: 'Funding Protocols', icon: Power },
        { path: '/dashboard/ventures', label: 'Ventures', icon: Users },
        { path: '/dashboard/legal', label: 'Legal', icon: FileText },
        { path: '/dashboard/tax', label: 'Tax', icon: FileText },
        { path: '/dashboard/profile', label: 'Profile', icon: Users },
        { path: '/dashboard/risk', label: 'Risk', icon: Shield },
    ];

    const [systemsOpen, setSystemsOpen] = React.useState(false);

    const isActiveLink = (path) => {
        if (path === '/dashboard') return location.pathname === '/dashboard';
        return location.pathname.startsWith(path);
    };

    return (
        <aside className={cn(
            'bg-burgundy-black flex flex-col transition-all duration-300 ease-in-out text-white fixed left-0 top-0 h-full z-50',
            isMinimized ? 'w-20' : 'w-64'
        )}>
            {/* Logo Header - Clickable to toggle sidebar */}
            <div 
                className="h-20 flex items-center justify-center cursor-pointer p-4 flex-shrink-0 hover:bg-white/5 transition-colors" 
                onClick={onToggle}
                title={isMinimized ? "Expand sidebar" : "Collapse sidebar"}
            >
                {isMinimized ? 
                    <LogoIcon className="h-12 w-12 mx-auto" /> : 
                    <div className="text-2xl font-bold text-center font-serif whitespace-nowrap">
                        <span className="text-[#FF6B35]">Sans</span>
                        <span className="text-white" style={{textShadow: '0 0 10px rgba(255, 255, 255, 0.8)'}}>Mercantile</span>
                        <sup className="text-white text-xs">™</sup>
                    </div>
                }
            </div>

            {/* Demo Mode Toggle - Only show if not locked */}
            {!isDemoLocked && (
                <div className={cn('px-4 py-3 border-b border-white/10', isMinimized && 'px-2')}>
                    <div className={cn('flex items-center', isMinimized ? 'justify-center' : 'justify-between')}>
                        {!isMinimized && (
                            <span className="text-sm text-gray-400">Mode:</span>
                        )}
                        <button
                            onClick={onDemoModeToggle}
                            className={cn(
                                'relative inline-flex items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-white',
                                isMinimized ? 'h-8 w-8' : 'h-6 w-11',
                                demoMode ? 'bg-orange-500' : 'bg-green-500'
                            )}
                            title={demoMode ? 'Demo Mode (Free Data)' : 'Live Mode (Real-time Data)'}
                        >
                            <span className="sr-only">Toggle demo mode</span>
                            {!isMinimized && (
                                <span
                                    className={cn(
                                        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                                        demoMode ? 'translate-x-6' : 'translate-x-1'
                                    )}
                                />
                            )}
                            {isMinimized && (
                                <Power className="h-5 w-5 mx-auto" />
                            )}
                        </button>
                        {!isMinimized && (
                            <span className={cn('text-xs font-semibold', demoMode ? 'text-orange-400' : 'text-green-400')}>
                                {demoMode ? 'DEMO' : 'LIVE'}
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Demo Mode Locked Indicator */}
            {isDemoLocked && (
                <div className={cn('px-4 py-3 border-b border-white/10 bg-orange-500/10', isMinimized && 'px-2')}>
                    {!isMinimized ? (
                        <div className="flex items-center justify-center space-x-2">
                            <Power className="h-4 w-4 text-orange-400" />
                            <span className="text-xs font-semibold text-orange-400">DEMO MODE</span>
                        </div>
                    ) : (
                        <Power className="h-5 w-5 mx-auto text-orange-400" />
                    )}
                </div>
            )}

            {/* Navigation */}
            <nav className="flex-grow flex flex-col overflow-y-auto">
                <div className="space-y-2 w-full px-2 py-4">
                    {/* Main navigation */}
                    {navItems.map(item => (
                        <Link 
                            key={item.path} 
                            to={item.path} 
                            className={cn(
                                'icon-btn w-full flex items-center rounded-lg transition-all duration-200',
                                isActiveLink(item.path) && 'active bg-white/10',
                                isMinimized ? 'justify-center p-3' : 'px-4 py-3'
                            )} 
                            title={item.label}
                        >
                            <item.icon size={20} />
                            {!isMinimized && <span className="ml-3 font-medium text-sm">{item.label}</span>}
                        </Link>
                    ))}

                    {/* Collapsible Systems section */}
                    {!isMinimized && (
                        <div className="w-full">
                            <button
                                className="icon-btn w-full flex items-center px-4 py-3 rounded-lg font-medium text-sm"
                                onClick={() => setSystemsOpen(!systemsOpen)}
                                title="Systems"
                            >
                                <BarChart4 size={20} />
                                <span className="ml-3">Systems</span>
                                <span className="ml-auto text-xs">{systemsOpen ? '▲' : '▼'}</span>
                            </button>
                            {systemsOpen && (
                                <div className="ml-8 mt-2 space-y-2">
                                    {systemsItems.map(item => (
                                        <Link 
                                            key={item.path} 
                                            to={item.path} 
                                            className={cn(
                                                'icon-btn w-full flex items-center px-3 py-2 rounded-lg transition-all duration-200',
                                                isActiveLink(item.path) && 'active bg-white/10'
                                            )} 
                                            title={item.label}
                                        >
                                            <item.icon size={18} />
                                            <span className="ml-3 text-sm">{item.label}</span>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </nav>

            {/* Footer spacer */}
            <div className="h-20 flex-shrink-0"></div>
        </aside>
    );
}