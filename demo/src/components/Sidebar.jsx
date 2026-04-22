import React from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  Brain, 
  Users, 
  Database, 
  Shield, 
  Zap,
  FileText
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, section: 'dashboard' },
  { name: 'AGI Core', icon: Brain, section: 'agi-core' },
  { name: 'Multi-Agent', icon: Users, section: 'multi-agent' },
  { name: 'Data Ingestion', icon: Database, section: 'data-ingestion' },
  { name: 'Security', icon: Shield, section: 'security' },
  { name: 'Automation', icon: Zap, section: 'automation' },
  { name: 'Tax Intelligence', icon: FileText, section: 'tax' },
];

const Sidebar = ({ activeSection, setActiveSection, device = 'desktop' }) => {
  const isMobile = device === 'mobile';
  return (
    <>
      {isMobile ? (
        <motion.header className="fixed top-0 left-0 right-0 p-3 flex items-center justify-between bg-black/60 z-50 border-b border-green-500/10">
          <div className="flex items-center space-x-3">
            <img  alt="Sans Mercantile Logo" className="w-8 h-8 rounded" src="https://images.unsplash.com/photo-1585065799297-ce07d1855c01" />
            <div className="text-sm font-medium">PRIV Core — Mobile</div>
          </div>
        </motion.header>
      ) : (
        <motion.aside 
          className="w-64 fixed top-0 left-0 h-full bg-black/50 backdrop-blur-lg p-4 flex flex-col z-40 border-r border-green-500/20"
      initial={{ x: -256 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex items-center space-x-3 mb-10">
        <img  alt="Sans Mercantile Logo" className="w-10 h-10" src="https://images.unsplash.com/photo-1585065799297-ce07d1855c01" />
        <div className="flex flex-col">
            <span className="font-bold text-lg text-white">SANS</span>
            <span className="text-xs text-gray-400 -mt-1">MERCANTILE</span>
        </div>
      </div>
      
      <nav className="flex-1">
        <ul>
          {navItems.map((item) => {
            const isActive = activeSection === item.section;
            return (
              <li key={item.name} className="mb-2">
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setActiveSection(item.section);
                  }}
                  className={`flex items-center p-3 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-green-500/20 text-white'
                      : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
                  }`}
                >
                  <item.icon className={`w-5 h-5 mr-3 ${isActive ? 'text-green-400' : ''}`} />
                  <span className="font-medium">{item.name}</span>
                  {isActive && (
                    <motion.div
                      layoutId="active-indicator"
                      className="w-1 h-6 bg-green-400 rounded-full ml-auto"
                    ></motion.div>
                  )}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

          <div className="mt-auto">
            <div className="p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-300">System Status:</p>
              <div className="flex items-center space-x-2 mt-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400 font-medium text-sm">All Systems Optimal</span>
              </div>
            </div>
          </div>
        </motion.aside>
      )}
    </>
  );
};

export default Sidebar;
