import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
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
import UnifiedAssistant from "./ui/UnifiedAssistant";
import GuidedWalkthrough from "./components/GuidedWalkthrough";
import { initDatadog } from "./lib/datadog";

interface AppProps {
  initialDevice?: string;
}

function App({ initialDevice = "desktop" }: AppProps) {
  const location = useLocation();
  const [isWalkthroughActive, setWalkthroughActive] = useState(false);
  const [device, setDevice] = useState(initialDevice);
  const [isSidebarMinimized, setSidebarMinimized] = useState(false);
  const [demoMode, setDemoMode] = useState<boolean>(() => {
    // Load demo mode from localStorage or default to true
    const saved = localStorage.getItem("demoMode");
    return saved !== null ? JSON.parse(saved) : true;
  });

  useEffect(() => {
    initDatadog();
    const hasSeenWalkthrough = localStorage.getItem("hasSeenWalkthrough");
    if (!hasSeenWalkthrough) {
      setWalkthroughActive(true);
      localStorage.setItem("hasSeenWalkthrough", "true");
    }
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

  const handleToggleDemoMode = () => {
    setDevice(prev => prev); // keep state intact
    setDemoMode(!demoMode);
  };

  const handleEndWalkthrough = () => {
    setWalkthroughActive(false);
  };

  return (
    <>
      <div className={`min-h-screen bg-black neural-grid matrix-bg device-${device}`}>
        {isWalkthroughActive && <GuidedWalkthrough onEnd={handleEndWalkthrough} />}
        
        {/* Demo Mode Banner */}
        {demoMode && (
          <div className="fixed top-0 left-0 right-0 bg-orange-500/90 text-white text-center py-2 text-sm font-semibold z-40 backdrop-blur-sm">
            🎭 DEMO MODE - Using free public data sources (delayed ~15 min)
          </div>
        )}
        
        <div className="flex" style={{ paddingTop: demoMode ? "40px" : "0" }}>
          <Sidebar 
            device={device} 
            setDevice={setDevice}
            isMinimized={isSidebarMinimized}
            onToggle={handleToggleSidebar}
            demoMode={demoMode}
            onDemoModeToggle={handleToggleDemoMode}
            isDemoLocked={false}
          />
          
          <main className={`flex-1 transition-all duration-300 ${isSidebarMinimized ? "ml-20" : "ml-64"}`}>
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="p-6"
              >
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard demoMode={demoMode} />} />
                  <Route path="/dashboard/terminal" element={<TradingTerminal demoMode={demoMode} setDemoMode={setDemoMode} />} />
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
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
        
        <UnifiedAssistant isVisible={true} />
        <Toaster />
      </div>
    </>
  );
}

export default App;
