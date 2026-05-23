import React from "react";
import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  Brain, 
  Users, 
  Activity, 
  ShieldCheck, 
  Terminal, 
  Landmark,
  Newspaper,
  BarChart2,
  History,
  Link2,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Smartphone,
  Laptop,
  Coins,
  UserCircle,
  FileCheck,
  Plug,
  Bell,
  Gauge,
  Lightbulb,
  Eye,
  Mic,
  Wallet,
  Banknote,
  Briefcase,
  Scale,
  Send,
  Vault,
  Shield
} from "lucide-react";
import logo from "../assets/images/logo_1779280505672.png";

interface SidebarProps {
  device: string;
  setDevice: (dev: string) => void;
  isMinimized: boolean;
  onToggle: () => void;
  demoMode: boolean;
  onDemoModeToggle: () => void;
  isDemoLocked?: boolean;
}

export interface SectionItem {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
}

export const navigationItems: SectionItem[] = [
  { name: "Live Dashboard", icon: LayoutDashboard, path: "/dashboard" },
  { name: "Broker Terminal", icon: Coins, path: "/dashboard/terminal" },
  { name: "AGI Core", icon: Brain, path: "/dashboard/agi-core" },
  { name: "Multi-Agent Hub", icon: Users, path: "/dashboard/multi-agent" },
  { name: "Data Ingest", icon: Activity, path: "/dashboard/data-ingestion" },
  { name: "Security Check", icon: ShieldCheck, path: "/dashboard/security" },
  { name: "Automation System", icon: Terminal, path: "/dashboard/automation" },
  { name: "Tax Intelligence", icon: Landmark, path: "/dashboard/tax" },
  { name: "Tactical News", icon: Newspaper, path: "/dashboard/news" },
  { name: "Diagnostics Log", icon: BarChart2, path: "/dashboard/analytics" },
  { name: "History & Audit", icon: History, path: "/dashboard/history" },
  { name: "SANS Network Link", icon: Link2, path: "/dashboard/connections" },
];

export const accountNavigationItems: SectionItem[] = [
  { name: "Profile & Preferences", icon: UserCircle, path: "/dashboard/profile" },
  { name: "KYC Verification", icon: FileCheck, path: "/dashboard/kyc" },
  { name: "Broker Accounts", icon: Plug, path: "/dashboard/broker-connect" },
  { name: "Trade Alerts", icon: Bell, path: "/dashboard/alerts" },
  { name: "Risk Analysis", icon: Gauge, path: "/dashboard/risk" },
  { name: "Market Insights", icon: Lightbulb, path: "/dashboard/insights" },
  { name: "Vision Analysis", icon: Eye, path: "/dashboard/vision" },
  { name: "Audio Intel", icon: Mic, path: "/dashboard/audio" },
  { name: "Wallet", icon: Wallet, path: "/dashboard/wallet" },
  { name: "Funding", icon: Banknote, path: "/dashboard/funding" },
  { name: "Ventures", icon: Briefcase, path: "/dashboard/ventures" },
  { name: "Legal", icon: Scale, path: "/dashboard/legal" },
  { name: "Trade Executor", icon: Send, path: "/dashboard/trade-executor" },
  { name: "Treasury", icon: Vault, path: "/dashboard/treasury" },
  { name: "System Integrity", icon: Shield, path: "/dashboard/integrity" },
];

export default function Sidebar({
  device,
  setDevice,
  isMinimized,
  onToggle,
  demoMode,
  onDemoModeToggle,
  isDemoLocked = false
}: SidebarProps) {
  const isMobile = device === "mobile";

  // Mobile Top Bar
  if (isMobile) {
    return (
      <header className="fixed top-0 left-0 right-0 h-16 px-4 flex items-center justify-between bg-black/95 border-b border-white/10 z-50 backdrop-blur-md">
        <div className="flex items-center space-x-2">
          <img 
            alt="Sans Mercantile Logo" 
            className="w-7 h-7 object-cover rounded border border-white/25" 
            src={logo} 
            referrerPolicy="no-referrer"
          />
          <span className="font-serif italic text-white font-medium text-sm tracking-wide">Priv Core</span>
        </div>
        
        {/* Horizontal Navigation List */}
        <div className="flex items-center space-x-1.5 overflow-x-auto max-w-[200px] sm:max-w-none scrollbar-hide py-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/dashboard"}
                className={({ isActive }) => `p-1.5 rounded transition ${
                  isActive 
                    ? "bg-white/10 text-white border border-white/25" 
                    : "text-zinc-500 hover:text-white"
                }`}
                title={item.name}
              >
                <Icon className="w-4 h-4" />
              </NavLink>
            );
          })}
        </div>
        
        {/* Device Switcher (Mobile toggles to desktop) */}
        <button 
          onClick={() => setDevice("desktop")} 
          className="p-1.5 rounded bg-white/5 border border-white/10 text-white cursor-pointer"
          title="Switch to Desktop Mode"
        >
          <Laptop className="w-3.5 h-3.5" />
        </button>
      </header>
    );
  }

  // Desktop Main Sidebar
  return (
    <aside 
      className={`fixed top-0 left-0 h-screen bg-black/95 border-r border-white/10 transition-all duration-300 z-50 flex flex-col p-4 ${
        isMinimized ? "w-20" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className={`flex items-center space-x-3 mb-8 mt-2 pb-4 border-b border-white/5 ${isMinimized ? "justify-center" : ""}`}>
        <img 
          alt="Sans Mercantile Logo" 
          className="w-9 h-9 object-cover rounded border border-white/30" 
          src={logo} 
          referrerPolicy="no-referrer"
        />
        {!isMinimized && (
          <div>
            <h2 className="font-serif italic text-[#ffffff] tracking-wide text-lg leading-none font-medium">Priv Core</h2>
            <span className="text-[9px] text-zinc-500 font-mono tracking-widest mt-1 block uppercase">SANS MERCANTILE</span>
          </div>
        )}
      </div>

      {/* Navigation list */}
      <nav className="flex-1 space-y-1 overflow-y-auto scrollbar-hide">
        {!isMinimized && (
          <div className="px-3 py-1 text-[8px] font-mono text-zinc-600 tracking-widest uppercase">Core</div>
        )}
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/dashboard"}
              className={({ isActive }) => `flex items-center rounded-lg py-2.5 px-3 font-mono text-xs transition duration-200 border relative group overflow-hidden ${
                isActive 
                  ? "text-white bg-white/10 border-white/25 font-bold" 
                  : "text-zinc-400 border-transparent hover:text-white hover:bg-white/5"
              } ${isMinimized ? "justify-center" : "space-x-3"}`}
              title={isMinimized ? item.name : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!isMinimized && <span>{item.name}</span>}
              {!isMinimized && (
                <div className="absolute right-2 text-[8px] font-mono text-zinc-600 opacity-0 group-hover:opacity-100 transition duration-200">
                  EXEC
                </div>
              )}
            </NavLink>
          );
        })}
        {!isMinimized && (
          <div className="px-3 pt-4 pb-1 text-[8px] font-mono text-zinc-600 tracking-widest uppercase">Account & Platform</div>
        )}
        {accountNavigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `flex items-center rounded-lg py-2 px-3 font-mono text-xs transition duration-200 border ${
                isActive
                  ? "text-white bg-white/10 border-white/25 font-bold"
                  : "text-zinc-500 border-transparent hover:text-white hover:bg-white/5"
              } ${isMinimized ? "justify-center" : "space-x-3"}`}
              title={isMinimized ? item.name : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {!isMinimized && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Control Utility Bottom Box */}
      <div className="mt-auto space-y-4 pt-4 border-t border-white/5 font-mono text-[10px]">
        {/* Minifier, Demo toggler, Device preview */}
        <div className="space-y-2">
          {/* Demo Toggler */}
          <button 
            onClick={onDemoModeToggle}
            className={`w-full py-2 px-3 rounded flex items-center justify-between border cursor-pointer select-none transition ${
              demoMode 
                ? "bg-orange-500/10 border-orange-500/30 text-orange-400" 
                : "bg-white/3 border-white/5 text-zinc-400 hover:text-white"
            }`}
          >
            {!isMinimized ? (
              <>
                <span>DEMO ENVIRONMENT</span>
                <span className="text-[8px] px-1 bg-white/10 rounded">{demoMode ? "ON" : "OFF"}</span>
              </>
            ) : (
              <Sparkles className="w-3.5 h-3.5 mx-auto" />
            )}
          </button>

          {/* Toggle minimizer */}
          <button 
            onClick={onToggle}
            className="w-full py-1.5 px-3 rounded bg-white/3 border border-white/5 text-zinc-400 hover:text-white flex items-center justify-between cursor-pointer"
          >
            {!isMinimized ? (
              <>
                <span>MINIMIZE SIDEBAR</span>
                <ChevronLeft className="w-3.5 h-3.5" />
              </>
            ) : (
              <ChevronRight className="w-3.5 h-3.5 mx-auto" />
            )}
          </button>

          {/* Device toggle (desktop vs mobile) */}
          <div className="flex gap-1.5">
            <button 
              onClick={() => setDevice("desktop")} 
              className={`flex-1 py-1 px-2 rounded flex justify-center items-center border cursor-pointer transition ${
                device === "desktop" ? "bg-white/10 text-white border-white/20" : "bg-[#0c0c0c] border-transparent text-zinc-500"
              }`}
            >
              <Laptop className="w-3.5 h-3.5" />
            </button>
            <button 
              onClick={() => setDevice("mobile")} 
              className={`flex-1 py-1 px-2 rounded flex justify-center items-center border cursor-pointer transition ${
                device === "mobile" ? "bg-white/10 text-white border-white/20" : "bg-[#0c0c0c] border-transparent text-zinc-500"
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {!isMinimized && (
          <div className="border-t border-white/5 pt-3 text-[9px] text-zinc-600 font-semibold space-y-0.5 text-center">
            <div>SANS MERCANTILE CO.</div>
            <div className="tracking-wider">REIMAGINE &bull; REBUILD &bull; TRANSCEND</div>
          </div>
        )}
      </div>
    </aside>
  );
}
