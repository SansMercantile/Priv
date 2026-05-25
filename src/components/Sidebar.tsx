import React, { useState, useEffect } from "react";
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
  Menu,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Smartphone,
  Laptop,
  Coins,
  User
} from "lucide-react";
import logo from "../assets/images/logo_1779280505672.png";

// Adaptive glowing logo component that falls back to vector art if the image is empty or fails to load
const LogoIcon: React.FC<{ className?: string }> = ({ className = "w-9 h-9" }) => {
  const [imgFailed, setImgFailed] = useState(false);

  if (!imgFailed && logo) {
    return (
      <img
        alt="Sans Mercantile Logo"
        src={logo}
        referrerPolicy="no-referrer"
        onError={() => setImgFailed(true)}
        className={`${className} object-contain select-none max-w-full border-0 p-0 outline-none bg-transparent`}
        style={{
          filter: "drop-shadow(0 0 12px rgba(225, 29, 72, 0.95)) drop-shadow(0 0 3px rgba(159, 18, 57, 0.6))",
          border: "none"
        }}
      />
    );
  }

  return (
    <div className={`${className} flex items-center justify-center select-none bg-transparent`} style={{ border: "none" }}>
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
        style={{
          filter: "drop-shadow(0 0 10px #e11d48) drop-shadow(0 0 3px #9f1239)"
        }}
      >
        <path
          d="M50 15 L85 50 L50 85 L15 50 Z"
          stroke="url(#ruby-core-gradient)"
          strokeWidth="4"
          strokeLinejoin="round"
        />
        <path
          d="M50 28 L72 50 L50 72 L28 50 Z"
          fill="url(#ruby-core-gradient)"
          opacity="0.25"
        />
        <circle cx="50" cy="50" r="6" fill="#ffffff" />
        <defs>
          <linearGradient id="ruby-core-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff4b72" />
            <stop offset="50%" stopColor="#e11d48" />
            <stop offset="100%" stopColor="#9f1239" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

// Reusable elegant system name typing component
const TypingPriv: React.FC = () => {
  const [text, setText] = useState("");
  
  useEffect(() => {
    let typeTimer: any = null;
    const fullText = "Priv";
    
    const triggerEffect = () => {
      if (typeTimer) clearInterval(typeTimer);
      
      let index = 0;
      setText("");
      
      typeTimer = setInterval(() => {
        index++;
        if (index <= fullText.length) {
          setText(fullText.slice(0, index));
        } else {
          clearInterval(typeTimer);
          typeTimer = null;
        }
      }, 200);
    };

    // Begin typing effect on mount
    triggerEffect();

    // Loop typing every 10 minutes exactly (600,000 milliseconds)
    const systemInterval = setInterval(() => {
      triggerEffect();
    }, 10 * 60 * 1000);

    return () => {
      if (typeTimer) clearInterval(typeTimer);
      clearInterval(systemInterval);
    };
  }, []);

  return (
    <span className="relative inline-flex items-center select-none font-serif italic">
      <style>{`
        @keyframes priv-cursor-blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
      <span>{text}</span>
      <span 
        className="inline-block w-[2px] h-[0.85em] ml-1 shadow-[0_0_8px_#e11d48]"
        style={{ 
          backgroundColor: "#e11d48", // solid vibrant ruby/rose
          animation: "priv-cursor-blink 1.0s infinite",
          verticalAlign: "middle"
        }}
      />
    </span>
  );
};

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
  { name: "Priv Dashboard", icon: LayoutDashboard, path: "/dashboard" },
  { name: "Identity & Profile", icon: User, path: "/dashboard/profile" },
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
  { name: "SANS Network Link", icon: Link2, path: "/dashboard/connections" }
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
          <LogoIcon className="w-7 h-7" />
          <span className="font-serif italic text-white font-medium text-sm tracking-wide flex items-center">
            <TypingPriv />
          </span>
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
        <LogoIcon className="w-9 h-9" />
        {!isMinimized && (
          <div>
            <h2 className="font-serif italic text-[#ffffff] tracking-wide text-lg leading-none font-medium flex items-center">
              <TypingPriv />
            </h2>
            <span className="text-[#FF6B35]">Sans</span>
            <span className="text-white" style={{textShadow: '0 0 10px rgba(255, 255, 255, 0.8)'}}>Mercantile</span>
            <sup className="text-white text-xs">™</sup>
          </div>
        )}
      </div>

      {/* Navigation list */}
      <nav className="flex-1 space-y-1 overflow-y-auto scrollbar-hide">
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
            <div className="tracking-wider text-zinc-700">REIMAGINE &bull; REBUILD &bull; TRANSCEND</div>
            <div className="pt-1 select-none opacity-25 hover:opacity-100 transition-opacity duration-300">
              <NavLink 
                to="/dashboard/admin/kyc" 
                className="text-[7.5px] font-mono tracking-widest text-zinc-500 hover:text-rose-500 uppercase"
              >
                [Compliance Gate]
              </NavLink>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
