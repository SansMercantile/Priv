import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Toaster } from "./components/ui/toaster";
import Sidebar, { navigationItems, accountNavigationItems } from "./components/Sidebar";
import DemoEnvironmentNotice from "./components/DemoEnvironmentNotice";
import ProtectedRoute from "./components/ProtectedRoute";
import { useEnvironment } from "./context/EnvironmentContext";

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

import LoginPage from "./pages/LoginPage";
import CreateProfilePage from "./pages/CreateProfilePage";
import VerificationPage from "./pages/VerificationPage";
import ProfilePage from "./pages/ProfilePage";
import BrokerPage from "./pages/BrokerPage";
import ConnectionsPage from "./pages/ConnectionsPage";
import AlertsPage from "./pages/AlertsPage";
import RiskPage from "./pages/RiskPage";
import InsightsPage from "./pages/InsightsPage";
import VisionPage from "./pages/VisionPage";
import AudioPage from "./pages/AudioPage";
import NewsPage from "./pages/NewsPage";
import TaxPage from "./pages/TaxPage";
import WalletPage from "./pages/WalletPage";
import FundingPage from "./pages/FundingPage";
import VenturesPage from "./pages/VenturesPage";
import LegalPage from "./pages/LegalPage";
import TradeExecutorPage from "./pages/TradeExecutorPage";
import BrokerOAuthCallbackPage from "./pages/BrokerOAuthCallbackPage";
import TreasuryDashboard from "./components/TreasuryDashboard";
import SystemIntegrityDashboard from "./components/SystemIntegrityDashboard";
import LiveModeWelcome from "./components/LiveModeWelcome";

interface AppProps {
  initialDevice?: string;
}

function DashboardShell({ demoMode }: { demoMode: boolean }) {
  const location = useLocation();
  const [isWalkthroughActive, setWalkthroughActive] = useState(false);
  const [device, setDevice] = useState("desktop");
  const [isSidebarMinimized, setSidebarMinimized] = useState(false);
  const [noticeDismissed, setNoticeDismissed] = useState(false);
  const { toggleDemoMode } = useEnvironment();

  useEffect(() => {
    const hasSeenWalkthrough = localStorage.getItem("hasSeenWalkthrough");
    if (!hasSeenWalkthrough) {
      setWalkthroughActive(true);
      localStorage.setItem("hasSeenWalkthrough", "true");
    }
  }, []);

  useEffect(() => {
    if (demoMode) setNoticeDismissed(false);
  }, [demoMode]);

  useEffect(() => {
    document.title = `Sans Mercantile™ PRIV Core - AI-Driven Execution Engine ${demoMode ? "(Demo)" : "(Live)"}`;
  }, [demoMode]);

  const bannerOffset = demoMode && !noticeDismissed ? "88px" : "0";

  return (
    <div className={`min-h-screen bg-black neural-grid matrix-bg device-${device}`}>
      {isWalkthroughActive && <GuidedWalkthrough onEnd={() => setWalkthroughActive(false)} />}
      <DemoEnvironmentNotice dismissed={noticeDismissed} onDismiss={() => setNoticeDismissed(true)} />
      {!demoMode && <LiveModeWelcome />}

      <div className="flex" style={{ paddingTop: bannerOffset }}>
        <Sidebar
          device={device}
          setDevice={setDevice}
          isMinimized={isSidebarMinimized}
          onToggle={() => setSidebarMinimized(!isSidebarMinimized)}
          demoMode={demoMode}
          onDemoModeToggle={toggleDemoMode}
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
                <Route path="/dashboard/terminal" element={<TradingTerminal demoMode={demoMode} />} />
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
                <Route path="/dashboard/profile" element={<ProfilePage demoMode={demoMode} />} />
                <Route path="/dashboard/kyc" element={<VerificationPage demoMode={demoMode} />} />
                <Route path="/dashboard/broker" element={<BrokerPage demoMode={demoMode} />} />
                <Route path="/dashboard/broker-connect" element={<ConnectionsPage demoMode={demoMode} />} />
                <Route path="/dashboard/alerts" element={<AlertsPage demoMode={demoMode} />} />
                <Route path="/dashboard/risk" element={<RiskPage demoMode={demoMode} />} />
                <Route path="/dashboard/insights" element={<InsightsPage demoMode={demoMode} />} />
                <Route path="/dashboard/vision" element={<VisionPage demoMode={demoMode} />} />
                <Route path="/dashboard/audio" element={<AudioPage demoMode={demoMode} />} />
                <Route path="/dashboard/feed" element={<NewsPage demoMode={demoMode} />} />
                <Route path="/dashboard/wallet" element={<WalletPage demoMode={demoMode} />} />
                <Route path="/dashboard/funding" element={<FundingPage demoMode={demoMode} />} />
                <Route path="/dashboard/ventures" element={<VenturesPage demoMode={demoMode} />} />
                <Route path="/dashboard/legal" element={<LegalPage demoMode={demoMode} />} />
                <Route path="/dashboard/tax-studio" element={<TaxPage demoMode={demoMode} />} />
                <Route path="/dashboard/trade-executor" element={<TradeExecutorPage demoMode={demoMode} />} />
                <Route path="/dashboard/treasury" element={<TreasuryDashboard />} />
                <Route path="/dashboard/integrity" element={<SystemIntegrityDashboard />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <UnifiedAssistant isVisible={true} />
      <Toaster />
    </div>
  );
}

function App({ initialDevice = "desktop" }: AppProps) {
  const { demoMode } = useEnvironment();
  void initialDevice;

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/oauth/callback" element={<BrokerOAuthCallbackPage />} />
      <Route
        path="/create-profile"
        element={
          <ProtectedRoute level="session">
            <CreateProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/verification"
        element={
          <ProtectedRoute level="profile">
            <VerificationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/*"
        element={
          demoMode ? (
            <DashboardShell demoMode={true} />
          ) : (
            <ProtectedRoute level="dashboard">
              <DashboardShell demoMode={false} />
            </ProtectedRoute>
          )
        }
      />
    </Routes>
  );
}

export default App;
