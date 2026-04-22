import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet';
import { motion } from 'framer-motion';
import { Toaster } from './components/ui/toaster';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AGICore from './components/AGICore';
import MultiAgent from './components/MultiAgent';
import DataIngestion from './components/DataIngestion';
import Security from './components/Security';
import Automation from './components/Automation';
import Tax from './components/Tax';
import PrivAssistant from './components/PrivAssistant';
import GuidedWalkthrough from './components/GuidedWalkthrough';

function App({ initialDevice = 'desktop' }) {
  const [activeSection, setActiveSection] = useState('dashboard');
  const [isWalkthroughActive, setWalkthroughActive] = useState(false);
  const [device, setDevice] = useState(initialDevice);

  useEffect(() => {
    const hasSeenWalkthrough = localStorage.getItem('hasSeenWalkthrough');
    if (!hasSeenWalkthrough) {
      setWalkthroughActive(true);
      localStorage.setItem('hasSeenWalkthrough', 'true');
    }
  }, []);

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return <Dashboard setActiveSection={setActiveSection} />;
      case 'agi-core':
        return <AGICore />;
      case 'multi-agent':
        return <MultiAgent />;
      case 'data-ingestion':
        return <DataIngestion />;
      case 'security':
        return <Security />;
      case 'automation':
        return <Automation />;
      case 'tax':
        return <Tax />;
      default:
        return <Dashboard setActiveSection={setActiveSection} />;
    }
  };

  const handleEndWalkthrough = () => {
    setWalkthroughActive(false);
  };

  return (
    <>
      <Helmet>
        <title>Sans Mercantile™ PRIV Core - AI-Driven Execution Engine</title>
        <meta name="description" content="Next-generation AI-driven execution engine featuring AGI & AI cores, multi-agent systems, and advanced market analysis capabilities." />
        <meta property="og:title" content="Sans Mercantile™ PRIV Core - AI-Driven Execution Engine" />
        <meta property="og:description" content="Revolutionary dual-core AGI system with emotional intelligence and deep market analysis capabilities." />
      </Helmet>
      
  <div className={`min-h-screen bg-black neural-grid matrix-bg device-${device}`}>
        {isWalkthroughActive && <GuidedWalkthrough onEnd={handleEndWalkthrough} />}
        
        <div className="flex">
          <Sidebar activeSection={activeSection} setActiveSection={setActiveSection} device={device} setDevice={setDevice} />
          
          <main className="flex-1 ml-64">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className="p-6"
            >
              {renderContent()}
            </motion.div>
          </main>
        </div>
        
        <PrivAssistant />
        <Toaster />
      </div>
    </>
  );
}

export default App;
