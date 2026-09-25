import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Analytics as VercelAnalytics } from "@vercel/analytics/react";
import { Toaster } from "./components/ui/toaster";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/dashboard/RealTimeDashboard";
import TradingTerminal from "./components/TradingTerminal";
import AGICore from "./components/AgiCore";
import MultiAgent from "./components/MultiAgent";
import DataIngestion from "./components/DataIngestion";
import Security from "./components/Security";
import Automation from "./components/Automation";
import Tax from "./components/Tax";
import News from "./components/News";
import Analytics from "./components/Analytics";
import History from "./components/History";
import Connections from "./components/Connections";
import Billing from "./components/Billing";
import Celebrations from "./components/Celebrations";
import ProfilePage from "./components/profile/ProfilePage";
import KycAdminReviewPage from "./components/profile/KycAdminReviewPage";
import UnifiedAssistant from "./ui/UnifiedAssistant";
import GuidedWalkthrough from "./components/GuidedWalkthrough";
import LoginGate from "./components/auth/LoginGate";
import Landing from "./pages/Landing";
import { useBrokerConnections } from "./lib/useBrokerConnections";
import { initiateDerivLogin, isDerivCallback } from "./lib/derivAuth/oauth";
import { initDatadog } from "./lib/datadog";

interface AppProps {
  initialDevice?: string;
}

function GatedApp({ initialDevice = "desktop" }: AppProps) {
  const location = useLocation();
  const [isWalkthroughActive, setWalkthroughActive] = useState(false);
  const [device, setDevice] = useState(initialDevice);
  const [isSidebarMinimized, setSidebarMinimized] = useState(false);
  const [demoMode, setDemoMode] = useState<boolean>(() => {
    // Load demo mode from localStorage or default to true
    const saved = localStorage.getItem("demoMode");
    return saved !== null ? JSON.parse(saved) : true;
  });

  const { hasRealDeriv, loading: brokerConnLoading } = useBrokerConnections();

  useEffect(() => {
    const hasSeenWalkthrough = localStorage.getItem("hasSeenWalkthrough");
    if (!hasSeenWalkthrough) {
      setWalkthroughActive(true);
      localStorage.setItem("hasSeenWalkthrough", "true");
    }

    // Auto-detect responsive orientation and screen sizing for handheld devices
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setDevice("mobile");
      } else {
        setDevice("desktop");
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Save demo mode to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem("demoMode", JSON.stringify(demoMode));
    // Also set environment variable for backend
    if (window.ENV) {
      window.ENV.DEMO_MODE = demoMode;
    }
  }, [demoMode]);

  // Programmatically update index metadata to side-step react-helmet warnings
  useEffect(() => {
    document.title = `Sans Mercantile™ PRIV Core - AI-Driven Execution Engine ${demoMode ? "(Demo Mode)" : ""}`;
    const updateMetaTag = (selector: string, keyName: "name" | "property", keyValue: string, val: string) => {
      let element = document.querySelector(selector);
      if (!element) {
        element = document.createElement("meta");
        element.setAttribute(keyName, keyValue);
        document.head.appendChild(element);
      }
      element.setAttribute("content", val);
    };
    updateMetaTag('meta[name="description"]', 'name', 'description', 'Next-generation AI-driven execution engine featuring AGI & AI cores, multi-agent systems, and advanced market analysis capabilities.');
    updateMetaTag('meta[property="og:title"]', 'property', 'og:title', 'Sans Mercantile™ PRIV Core - AI-Driven Execution Engine');
    updateMetaTag('meta[property="og:description"]', 'property', 'og:description', 'Revolutionary dual-core AGI system with emotional intelligence and deep market analysis capabilities.');
  }, [demoMode]);

  const handleToggleSidebar = () => {
    setSidebarMinimized(!isSidebarMinimized);
  };

  const handleToggleDemoMode = async () => {
    setDevice(prev => prev); // keep state intact
    // Only demo -> real is gated. If no real Deriv account is connected,
    // run the client-side PKCE flow via auth.deriv.com (the backend-driven
    // oauth.deriv.com route is dead -- Deriv bounces it to marketing).
    // After Deriv's login + consent screen it redirects back here with a
    // code, which LoginGate exchanges and hands to the backend.
    if (demoMode && !hasRealDeriv) {
      try {
        await initiateDerivLogin();
      } catch (e: any) {
        console.error("Deriv login failed to start:", e?.message || e);
      }
      return;
    }
    setDemoMode(!demoMode);
  };

  const handleEndWalkthrough = () => {
    setWalkthroughActive(false);
  };

  return (
    <LoginGate>
      <div className={`min-h-screen bg-black neural-grid matrix-bg device-${device}`}>
        {isWalkthroughActive && <GuidedWalkthrough onEnd={handleEndWalkthrough} />}
        
        {/* Demo Mode Banner */}
        {demoMode && (
          <div className="fixed top-0 left-0 right-0 bg-gradient-to-r from-black via-[#1c080d] to-black border-b border-rose-500/30 text-xs font-mono text-rose-200 py-2.5 px-4 z-40 backdrop-blur-md flex items-center justify-center gap-3 shadow-[0_2px_15px_rgba(225,29,72,0.12)]">
            <svg className="w-5 h-5 flex-shrink-0" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="rose-glow" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#ff4b72" />
                  <stop offset="100%" stopColor="#e11d48" />
                </linearGradient>
                <style>{`
                  @keyframes sway {
                    0%, 100% { transform: translateY(0px) rotate(-3deg); }
                    50% { transform: translateY(-2px) rotate(3deg); }
                  }
                  .sway-group { 
                    animation: sway 5s infinite ease-in-out; 
                    transform-origin: 16px 16px; 
                  }
                  .comedy-glow {
                    filter: drop-shadow(0 0 3px #e11d48);
                  }
                `}</style>
              </defs>
              <g className="sway-group">
                {/* Background Tragedy Mask */}
                <g transform="translate(-1, 2) scale(0.9)" opacity="0.5">
                  <path d="M12 4C7 4 4 7 4 12C4 18 8 22 12 25C16 22 20 18 20 12C20 7 17 4 12 4Z" stroke="url(#rose-glow)" strokeWidth="1.5" />
                  <circle cx="9" cy="11" r="1.2" fill="#ff4b72" />
                  <circle cx="15" cy="11" r="1.2" fill="#ff4b72" />
                  <path d="M9 17C10 16 14 16 15 17" stroke="#e11d48" strokeWidth="1.5" strokeLinecap="round" />
                </g>
                {/* Foreground Comedy Mask */}
                <g transform="translate(6, 0) scale(0.95)" className="comedy-glow">
                  <path d="M14 3C9 3 6 6 6 11C6 17 10 21 14 24C18 21 22 17 22 11C22 6 19 3 14 3Z" fill="#120206" stroke="#ff4b72" strokeWidth="1.8" />
                  <path d="M10 10C11 9 12 9 13 10" stroke="#ff4b72" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M15 10C16 9 17 9 18 10" stroke="#ff4b72" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M10 15C11 17 17 17 18 15" stroke="#ff4b72" strokeWidth="1.5" strokeLinecap="round" fill="none" />
                </g>
              </g>
            </svg>
            <span className="tracking-widest text-[9px] sm:text-xs">
              <span className="text-[#ff4b72] font-semibold">DEMO ENVIRONMENT</span> — USING COBALT-RATED DELAYED DATA INDEXING (SANS SECURE PUBLIC ROUTER)
            </span>
          </div>
        )}
        
        <div className="flex" style={{ paddingTop: device === "mobile" ? (demoMode ? "106px" : "64px") : (demoMode ? "42px" : "0") }}>
          <Sidebar 
            device={device} 
            setDevice={setDevice}
            isMinimized={isSidebarMinimized}
            onToggle={handleToggleSidebar}
            demoMode={demoMode}
            onDemoModeToggle={handleToggleDemoMode}
            isDemoLocked={!hasRealDeriv && !brokerConnLoading}
          />
          
          <main className={`flex-1 transition-all duration-300 ${device === "mobile" ? "ml-0 pt-0" : isSidebarMinimized ? "ml-20" : "ml-64"}`}>
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="p-4 sm:p-6"
              >
                <Routes>
                  <Route path="/dashboard" element={<Dashboard demoMode={demoMode} />} />
                  <Route path="/dashboard/terminal" element={<TradingTerminal />} />
                  <Route path="/dashboard/agi-core" element={<AGICore demoMode={demoMode} />} />
                  <Route path="/dashboard/multi-agent" element={<MultiAgent demoMode={demoMode} />} />
                  <Route path="/dashboard/data-ingestion" element={<DataIngestion demoMode={demoMode} />} />
                  <Route path="/dashboard/security" element={<Security demoMode={demoMode} />} />
                  <Route path="/dashboard/automation" element={<Automation demoMode={demoMode} />} />
                  <Route path="/dashboard/tax" element={<Tax demoMode={demoMode} />} />
                  <Route path="/dashboard/news" element={<News demoMode={demoMode} />} />
                  <Route path="/dashboard/analytics" element={<Analytics demoMode={demoMode} />} />
                  <Route path="/dashboard/history" element={<History demoMode={demoMode} />} />
                  <Route path="/dashboard/connections" element={<Connections demoMode={demoMode} />} />
                  <Route path="/dashboard/billing" element={<Billing demoMode={demoMode} />} />
                  <Route path="/dashboard/profile" element={<ProfilePage demoMode={demoMode} />} />
                  <Route path="/dashboard/admin/kyc" element={<KycAdminReviewPage />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
        
        <UnifiedAssistant isVisible={true} />
        <Celebrations />
        <Toaster />
        <VercelAnalytics />
      </div>
    </LoginGate>
  );
}

function App({ initialDevice = "desktop" }: AppProps) {
  useEffect(() => {
    initDatadog();
  }, []);

  return (
    <Routes>
      {/* Public marketing page for visitors before login -- EXCEPT when
          Deriv's PKCE return lands here (its registered Redirect URL is
          the bare origin "/", same as this route). React Router picks the
          exact "/" match over the "/*" catch-all below, so without this
          guard every Deriv return rendered Landing instead of GatedApp --
          LoginGate (which owns the code exchange + /connect-token POST +
          callback-ping telemetry) never mounted at all, silently
          swallowing 100% of Deriv connect attempts. isDerivCallback()
          checks for ?code&state (Deriv's shape); Auth0's own callback is a
          separate /callback route and is unaffected. */}
      <Route
        path="/"
        element={isDerivCallback() ? <GatedApp initialDevice={initialDevice} /> : <Landing />}
      />
      {/* Everything else behind the login gate */}
      <Route path="/*" element={<GatedApp initialDevice={initialDevice} />} />
    </Routes>
  );
}

export default App;
