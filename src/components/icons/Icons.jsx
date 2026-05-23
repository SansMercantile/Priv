// src/components/icons/Icons.jsx
import React from 'react';
import { motion } from 'framer-motion';

// Your custom image icons
export const LogoIcon = (props) => (<img src="/logo.svg" alt="Sans Mercantile Logo" {...props} />);
export const PrivAvatar = (props) => (<img src="/priv-avatar.svg" alt="Priv AI Avatar" {...props} />);

// Re-export all needed icons from lucide-react
export { 
    Shield, 
    LayoutDashboard, 
    LogOut, 
    User, 
    BarChart4, 
    Landmark, 
    MessageSquare, 
    Send, 
    TrendingDown, 
    History, 
    Wallet, 
    CheckCircle, 
    Mail, 
    Lock,
    Settings,
    FileText,
    Mic, 
    Camera,
    StopCircle,
    Brain, 
    Database, 
    Zap
} from 'lucide-react';