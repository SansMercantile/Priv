import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import KycVerificationPage from './KycVerificationPage';
import DerivConnectCard from '../DerivConnectCard';
import apiClient from '../../api/apiClient';
import { 
  User, 
  CreditCard, 
  Shield,
  Link2,
  Landmark, 
  Calendar, 
  DollarSign, 
  ExternalLink, 
  Cpu, 
  Coins, 
  RefreshCw, 
  CheckCircle2,
  TrendingUp,
  AlertTriangle,
  Flame,
  Gauge,
  Play,
  Pause,
  ArrowRight,
  Info,
  HelpCircle,
  Activity,
  Award
} from 'lucide-react';

interface UserProfileEditorProps {
  demoMode?: boolean;
}

interface BillingLog {
  id: string;
  time: string;
  action: string;
  impact: string;
  type: 'burn' | 'mint' | 'system';
}

export default function UserProfileEditor({ demoMode = false }: UserProfileEditorProps) {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'profile' | 'billing' | 'kyc' | 'brokers'>('profile');
  // Node Allocation & Credits is an admin surface (plan pricing, license
  // grants). Regular users never see the tab; admins do. (Effects live
  // below, after kycStatus is declared.)
  const [isAdmin, setIsAdmin] = useState(false);
  const [hasRealConnection, setHasRealConnection] = useState<boolean>(false);
  
  useEffect(() => {
    const checkConnections = () => {
      const bConn = localStorage.getItem("ex_conn_binance") === "true";
      const cConn = localStorage.getItem("ex_conn_coinbase") === "true";
      const isLogged = localStorage.getItem("xm_is_logged") === "true";
      setHasRealConnection(bConn || cConn || isLogged);
    };
    checkConnections();
    const interval = setInterval(checkConnections, 1200);
    return () => clearInterval(interval);
  }, []);
  
  // Custom temporary banner success messages (anti-iframe alert rules)
  const [profileSuccessMessage, setProfileSuccessMessage] = useState("");

  // Biometric Photo Avatar persistence
  const [avatarUrl, setAvatarUrl] = useState<string>(() => {
    return localStorage.getItem("xm_user_avatar") || "";
  });

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null;
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Str = reader.result as string;
      setAvatarUrl(base64Str);
      localStorage.setItem("xm_user_avatar", base64Str);
      window.dispatchEvent(new Event("priv_avatar_changed"));
    };
    reader.readAsDataURL(file);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("triggerKYC") === "true") {
      setActiveTab("kyc");
    }
  }, [location]);
  
  // Profile Parameters
  const [profile, setProfile] = useState(() => {
    const saved = localStorage.getItem("xm_user_profile");
    if (saved) {
      try { return JSON.parse(saved); } catch (_) {}
    }
    return {
      firstName: 'Alistair',
      lastName: 'Sterling',
      email: 'client@merchant.priv',
      phone: '+27 82 123 4567',
      country: 'South Africa',
      experience: '5+ years',
      riskAppetite: 'Aggressive',
      tradingGoal: 'Capital Expansion & Systematic Arbitrage'
    };
  });

  // Leverage & Custom Calibration Slider
  const [leverage, setLeverage] = useState<number>(() => {
    return parseInt(localStorage.getItem("xm_profile_leverage") || "20");
  });

  // Pricing & Licensing Node Tier
  const [nodeTier, setNodeTier] = useState<'standard' | 'obsidian' | 'sovereign'>(() => {
    return (localStorage.getItem("xm_node_tier") as any) || "obsidian";
  });

  // KYC Status Sync
  const [kycStatus, setKycStatus] = useState<string>(() => {
    return localStorage.getItem("xm_kyc_status") || "unsubmitted";
  });

  // Admin probe for the Node Allocation tab (see isAdmin above).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.get('/api/v1/admin/whoami');
        if (!cancelled && res?.data?.data?.admin) setIsAdmin(true);
      } catch (_) {
        /* stay non-admin */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  useEffect(() => {
    if (!isAdmin && activeTab === 'billing') setActiveTab('profile');
  }, [isAdmin, activeTab]);

  // Server truth for KYC status: after submit, poll the record so an
  // admin approve/reject flips this UI without a resubmit. Local status
  // is only the optimistic default.
  useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;
    const sync = async () => {
      try {
        const st: any = await apiClient.getKycStatus();
        const serverStatus = st?.status;
        if (!cancelled && serverStatus && serverStatus !== kycStatus) {
          setKycStatus(serverStatus);
          try {
            localStorage.setItem('xm_kyc_status', serverStatus);
          } catch (_) {}
        }
      } catch (_) {
        /* offline/anonymous: keep local status */
      }
    };
    if (kycStatus === 'submitted' || kycStatus === 'pending') {
      sync();
      timer = window.setInterval(sync, 30000);
    }
    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
    };
  }, [kycStatus]);

  // Billing & Usage Credits state
  const [credits, setCredits] = useState<number>(() => {
    const saved = localStorage.getItem("xm_usage_credits");
    return saved ? parseFloat(saved) : 842.15;
  });

  // Credit Gas Burner Pilot simulator state
  const [isPilotRunning, setIsPilotRunning] = useState<boolean>(false);
  const [liveLogQueue, setLiveLogQueue] = useState<BillingLog[]>([
    { id: 'TX-4819', time: '09:15:32 AM', action: 'Backtested AGI Empathy Stance EUR/USD', impact: '-0.30 PRIV', type: 'burn' },
    { id: 'TX-4818', time: '09:02:14 AM', action: 'Sovereign Clearing Portals Synchronized', impact: '0.00 PRIV', type: 'system' },
    { id: 'TX-3918', time: '08:44:02 AM', action: 'Obsidian Node License Allocation Allocated', impact: '+500.00 PRIV', type: 'mint' }
  ]);

  // Sync state modifications
  useEffect(() => {
    localStorage.setItem("xm_user_profile", JSON.stringify(profile));
    localStorage.setItem("xm_account_email", profile.email);
    localStorage.setItem("xm_user_risk_appetite", profile.riskAppetite);
  }, [profile]);

  useEffect(() => {
    localStorage.setItem("xm_profile_leverage", leverage.toString());
  }, [leverage]);

  useEffect(() => {
    localStorage.setItem("xm_node_tier", nodeTier);
  }, [nodeTier]);

  // Real-time synchronization
  useEffect(() => {
    const handleStatusSync = () => {
      const liveStatus = localStorage.getItem("xm_kyc_status") || "unsubmitted";
      setKycStatus(liveStatus);
      const savedCreds = localStorage.getItem("xm_usage_credits");
      if (savedCreds && !isPilotRunning) {
        setCredits(parseFloat(savedCreds));
      }
    };
    const interval = setInterval(handleStatusSync, 900);
    return () => clearInterval(interval);
  }, [isPilotRunning]);

  // Real-time gas credits burner simulator loops
  useEffect(() => {
    if (!isPilotRunning) return;

    const interval = setInterval(() => {
      setCredits(prev => {
        const nextCreds = Math.max(0, parseFloat((prev - 0.04).toFixed(2)));
        localStorage.setItem("xm_usage_credits", nextCreds.toString());
        return nextCreds;
      });

      // Append live operation log in real-time
      const timestamp = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const actions = [
        "Sweeping EUR/USD order book price anomalies",
        "ZKP block proof verified on SANS ledger",
        "Sovereign news feed polarity adjusted",
        "Arbitrage margin clearance updated at HMRC gate",
        "Sub-millisecond futures lot rebalancing executed"
      ];
      const randomAction = actions[Math.floor(Math.random() * actions.length)];
      const logId = `TX-${Math.floor(1000 + Math.random() * 9000)}`;
      
      setLiveLogQueue(prev => [
        { id: logId, time: timestamp, action: randomAction, impact: '-0.04 PRIV', type: 'burn' },
        ...prev.slice(0, 7)
      ]);
    }, 1200);

    return () => clearInterval(interval);
  }, [isPilotRunning]);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem("xm_user_profile", JSON.stringify(profile));
    localStorage.setItem("xm_user_risk_appetite", profile.riskAppetite);
    
    // Dispatch custom event to let other parts of application know about instantaneous updates
    window.dispatchEvent(new Event('storage'));
    
    setProfileSuccessMessage("Sovereign risk constraints & legal profile variables synchronized across SANS Node 04.");
    setTimeout(() => {
      setProfileSuccessMessage("");
    }, 4000);
  };

  const handleSponsorBoost = (amount: number) => {
    const added = amount === 100 ? 100 : amount === 250 ? 250 : 600;
    const finalCreds = parseFloat((credits + added).toFixed(2));
    setCredits(finalCreds);
    localStorage.setItem("xm_usage_credits", finalCreds.toString());

    const timestamp = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLiveLogQueue(prev => [
      { id: `MINT-${Math.floor(100 + Math.random() * 900)}`, time: timestamp, action: `Sponsored Node Allocation via SEC Desk (+${added} PRIV)`, impact: `+${added}.00 PRIV`, type: 'mint' },
      ...prev
    ]);
  };

  const handleRefreshCredits = () => {
    const newCreds = parseFloat((credits + 25.00).toFixed(2));
    setCredits(newCreds);
    localStorage.setItem("xm_usage_credits", newCreds.toString());
  };

  // S&P Grade Metrics Calculations based on user preference
  const getSPGrading = () => {
    switch (profile.riskAppetite) {
      case 'Conservative':
        return {
          grade: 'AAA / Sovereign Stable',
          desc: 'High-Capital Protection Shield. Margin buffers defense priority.',
          maxDrawdown: '1.2% Historical Outflow Range',
          varPercent: '0.8%',
          sharpRatio: '3.42 Optimal',
          kellyFraction: '0.12x (Fractional)',
          riskMultiplier: 0.5,
          color: 'text-emerald-400 border-emerald-900 bg-emerald-950/20'
        };
      case 'Moderate':
        return {
          grade: 'A- / Optimal Sharp Balance',
          desc: 'Balanced Systematic Arbitrage. Mid-term swing execution.',
          maxDrawdown: '4.5% Historical Outflow Range',
          varPercent: '3.2%',
          sharpRatio: '2.84 Robust',
          kellyFraction: '0.45x (Half-Kelly)',
          riskMultiplier: 1.0,
          color: 'text-sky-400 border-sky-900 bg-sky-950/20'
        };
      case 'Aggressive':
        return {
          grade: 'BB+ / Speculative Opportunity',
          desc: 'High-Yield Futures allocations. Sub-millisecond sweeps enabled.',
          maxDrawdown: '16.4% Historical Outflow Range',
          varPercent: '9.4%',
          sharpRatio: '1.92 Volatile',
          kellyFraction: '1.00x (Full-Kelly)',
          riskMultiplier: 2.0,
          color: 'text-[#e11d48] border-rose-900 bg-rose-950/20'
        };
      case 'Very aggressive':
        return {
          grade: 'CCC+ / High-Frequency Leverage',
          desc: 'Maximum leverage, flash collateral limits, high-slippage tolerances.',
          maxDrawdown: '38.5% Macro draw limits',
          varPercent: '24.1%',
          sharpRatio: '1.15 High-Beta',
          kellyFraction: '1.80x (Super-Kelly)',
          riskMultiplier: 4.5,
          color: 'text-amber-500 border-amber-900 bg-amber-950/20'
        };
      default:
        return {
          grade: 'A- / Optimal Balanced',
          desc: 'Standard default allocation strategy.',
          maxDrawdown: '4.5%',
          varPercent: '3.2%',
          sharpRatio: '2.84',
          kellyFraction: '0.45x',
          riskMultiplier: 1.0,
          color: 'text-white border-zinc-800 bg-zinc-900/40'
        };
    }
  };

  const spState = getSPGrading();

  // Dynamic values depending on selected leverage + risk
  const calculatedVar = parseFloat(spState.varPercent) * (leverage / 10);
  const calculatedMarginThreshold = Math.max(1, (100 / leverage) * 1.5).toFixed(2);
  const liquidationSpreadPercent = Math.max(0.01, (100 / leverage) * 0.85).toFixed(3);

  // Invoices history representation
  const invoices = [
    { id: 'INV-4820-2026', date: '2026-05-15', tier: 'PRIV Obsidian Node License', creditsAdded: '+500 PRIV', amount: '$150.00', status: 'Paid' },
    { id: 'INV-3918-2026', date: '2026-04-15', tier: 'PRIV Obsidian Node License', creditsAdded: '+500 PRIV', amount: '$150.00', status: 'Paid' },
    { id: 'INV-2081-2026', date: '2026-03-15', tier: 'PRIV Standard Allocation', creditsAdded: '+250 PRIV', amount: '$75.00', status: 'Paid' }
  ];

  return (
    <div className="space-y-6">
      
      {/* Mini tabs header resembling a trading desktop toolbar */}
      <div className="flex border-b border-zinc-900 pb-3 gap-2 overflow-x-auto scrollbar-hide">
        {[
          { id: 'profile', label: 'Sovereign Profile', icon: User },
          { id: 'brokers', label: 'Broker Connections', icon: Link2 },
          ...(isAdmin ? [{ id: 'billing', label: 'Node Allocation & Credits', icon: CreditCard }] : []),
          { id: 'kyc', label: 'Identity Registry KYC', icon: Shield }
        ].map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg font-mono text-xs font-bold transition duration-150 whitespace-nowrap cursor-pointer ${
                activeTab === t.id 
                  ? 'bg-rose-950/20 text-rose-400 border-rose-500/30 shadow-[0_0_8px_rgba(225,29,72,0.1)]' 
                  : 'bg-zinc-950/50 text-zinc-400 border-zinc-900 hover:text-white hover:bg-zinc-900/60'
              }`}
              id={`tab-btn-${t.id}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'profile' && (
        <div className="space-y-6">
          {hasRealConnection && (
            <div className="bg-rose-950/10 border border-rose-900/40 rounded-xl p-4 flex gap-4 pr-6">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse mt-1 flex-shrink-0" />
              <div className="space-y-1.5">
                <p className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <Shield className="w-4 h-4 text-rose-500" /> REAL INTEGRATED ACCOUNT ENDPOINT STATUS DETECTED
                </p>
                <p className="text-[11px] text-zinc-400 font-light leading-relaxed">
                  Compliance frameworks require you to submit your verified <strong>Sovereign Risk Tolerance</strong> profile, register your secure <strong>KYC document verification file</strong>, and finalize account credentials by uploading a signature profile image before executing trades on live broker indices.
                </p>
                <div className="pt-1 flex items-center gap-4">
                  <button
                    onClick={() => setActiveTab("kyc")}
                    className="px-3 py-1 bg-rose-900 hover:bg-rose-800 text-[10px] font-bold font-mono uppercase rounded text-white transition cursor-pointer"
                  >
                    Complete Identity KYC Section &rarr;
                  </button>
                  <label
                    htmlFor="account-avatar-uploader"
                    className="text-[10px] font-mono text-zinc-500 hover:text-rose-400 transition cursor-pointer underline decoration-dotted capitalize"
                  >
                    Choose Signature Image
                  </label>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            
            {/* Profile input parameters */}
            <div className="xl:col-span-2 space-y-6">
              <form onSubmit={handleSaveProfile} className="bg-zinc-900/20 border border-zinc-800/60 p-5 rounded-xl space-y-5">
                <h2 className="text-xs font-mono uppercase tracking-widest font-extrabold text-[#e11d48] border-b border-zinc-900 pb-2 flex items-center justify-between">
                  <span>1. Profile</span>
                  <span className="text-[9px] text-zinc-500 lowercase font-medium">Node 04 sync limits verified</span>
                </h2>

                {/* Biometric Avatar / Signature Photo upload section */}
                <div className="flex flex-col sm:flex-row items-center gap-4 bg-zinc-950/40 p-3.5 rounded-lg border border-zinc-900">
                  <div className="relative w-12 h-12 rounded-full bg-zinc-900 border border-zinc-850 flex items-center justify-center overflow-hidden flex-shrink-0">
                    {avatarUrl ? (
                      <img referrerPolicy="no-referrer" src={avatarUrl} alt="Executive Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-5 h-5 text-zinc-600" />
                    )}
                  </div>
                  <div className="space-y-1 flex-1 text-center sm:text-left">
                    <p className="text-[9px] font-mono text-zinc-400 uppercase font-black tracking-widest">Biometric signature photo</p>
                    <p className="text-[9px] text-zinc-500 font-mono">Upload professional file photo reference synchronized with Shufti biometric nodes.</p>
                    <div className="pt-0.5">
                      <input 
                        type="file" 
                        id="account-avatar-uploader" 
                        accept="image/*" 
                        onChange={handleAvatarChange} 
                        className="hidden" 
                      />
                      <label 
                        htmlFor="account-avatar-uploader" 
                        className="inline-block px-2.5 py-1 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:text-white rounded text-[9px] font-mono text-zinc-400 font-bold cursor-pointer transition"
                      >
                        Upload Signature Image
                      </label>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">First Legal Name</label>
                  <input 
                    type="text" 
                    value={profile.firstName} 
                    id="profile-firstName"
                    onChange={e => setProfile({...profile, firstName: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Last Legal Name</label>
                  <input 
                    type="text" 
                    value={profile.lastName} 
                    id="profile-lastName"
                    onChange={e => setProfile({...profile, lastName: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Identity verification Email</label>
                  <input 
                    type="email" 
                    value={profile.email} 
                    id="profile-email"
                    onChange={e => setProfile({...profile, email: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Handshake Phone Range</label>
                  <input 
                    type="text" 
                    value={profile.phone} 
                    id="profile-phone"
                    onChange={e => setProfile({...profile, phone: e.target.value})}
                    className="w-full p-2.5 bg-zinc-955 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Sovereign Origin Region</label>
                  <input 
                    type="text" 
                    value={profile.country} 
                    id="profile-country"
                    onChange={e => setProfile({...profile, country: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">System Experience Level</label>
                  <select 
                    value={profile.experience}
                    id="profile-experience"
                    onChange={e => setProfile({...profile, experience: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  >
                    <option value="None">None / Basic</option>
                    <option value="< 1 year">Under 1 Year</option>
                    <option value="1–3 years">1 to 3 Years</option>
                    <option value="3–5 years">3 to 5 Years</option>
                    <option value="5+ years">Professional (5+ Years)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">SANS Risk Tolerance Class</label>
                  <select 
                    value={profile.riskAppetite}
                    id="profile-riskAppetite"
                    onChange={e => {
                      setProfile({...profile, riskAppetite: e.target.value});
                    }}
                    className="w-full p-2.5 bg-zinc-950 text-white rounded border border-rose-900/50 font-mono text-xs text-rose-400 font-bold focus:outline-none focus:border-rose-500 transition"
                  >
                    <option value="Conservative">Conservative Safeguard</option>
                    <option value="Moderate">Moderate Balanced growth</option>
                    <option value="Aggressive">Aggressive Sovereign Arbitrage</option>
                    <option value="Very aggressive">Ultra High-Frequency Exposure</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Algorithmic Allocation Objective</label>
                  <input 
                    type="text" 
                    value={profile.tradingGoal} 
                    id="profile-tradingGoal"
                    onChange={e => setProfile({...profile, tradingGoal: e.target.value})}
                    className="w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                    placeholder="system expansion limits..."
                  />
                </div>
              </div>

              {/* Seamless Bloomberg-style Leverage Calibration Slider directly integrated */}
              <div className="pt-4 border-t border-zinc-900/60 space-y-3.5">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-[11px] font-mono text-zinc-300 font-bold uppercase tracking-wider">
                      2. Interactive Leverage Calibration
                    </label>
                    <span className="text-[9px] text-zinc-500 font-mono">
                      Dynamic order multiplier. Warning: BB+ and CCC risk limits can trigger flash liquidation loops.
                    </span>
                  </div>
                  <div className="px-3 py-1 bg-zinc-950 border border-[#e11d48]/40 rounded font-mono text-xs text-white">
                    LEVERAGE: <strong className="text-rose-500 text-sm">{leverage}X</strong>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span className="text-[10px] text-zinc-500 font-mono">1X (Safe)</span>
                  <input 
                    type="range" 
                    min="1" 
                    max="500" 
                    value={leverage}
                    onChange={e => setLeverage(parseInt(e.target.value))}
                    className="flex-1 accent-rose-600 cursor-pointer h-1.5 bg-zinc-950 rounded-lg appearance-none"
                  />
                  <span className="text-[10px] text-rose-500 font-mono font-bold">500X (Hyper-beta)</span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-3 text-right">
                <p className="text-[9px] font-mono text-zinc-500 leading-snug text-left max-w-sm">
                  * Synchronizing this deck auto-adjusts systemic leverage factors across the Broker Terminal and limits trade sizing margins.
                </p>
                <button 
                  type="submit"
                  id="btn-sync-profile"
                  className="px-5 py-2.5 bg-gradient-to-r from-rose-700 to-rose-600 hover:from-rose-600 hover:to-rose-500 text-white font-mono text-xs font-bold rounded-lg transition-all shadow-[0_4px_12px_rgba(225,29,72,0.15)] cursor-pointer"
                >
                  Sync Systemic Risk Constraints
                </button>
              </div>
            </form>
          </div>

          {/* Sovereign Capital Risk Index Visualizer Panel */}
          <div className="bg-zinc-905 p-5 border border-zinc-800/80 rounded-xl space-y-4.5 flex flex-col h-full bg-zinc-950/40">
            <div className="border-b border-zinc-900 pb-3 flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase tracking-widest font-extrabold text-zinc-400 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-rose-500" /> Sovereign Grading
              </h3>
              <span className="text-[8px] font-mono px-2 py-0.5 rounded border border-zinc-800 bg-zinc-950 text-zinc-500">
                STRESS LABS
              </span>
            </div>

            {/* Simulated Live Grade Card */}
            <div className={`p-4 border rounded-xl space-y-2 ${spState.color} transition-all duration-300`}>
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-mono uppercase tracking-wider text-zinc-400">Portfolio Rating Index</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/5 border border-white/10 uppercase tracking-widest">
                  LIVE STATUS
                </span>
              </div>
              <p className="text-xl font-mono font-extrabold tracking-tight italic text-white flex items-center">
                {spState.grade}
              </p>
              <p className="text-[11px] font-sans text-zinc-300 leading-relaxed font-light">
                {spState.desc}
              </p>
            </div>

            {/* Technical VaR & Multiplier Ratios */}
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Base Value-at-Risk (99% VaR)</span>
                <span className="text-white font-bold">{spState.varPercent} Daily Balance</span>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Adjusted VaR (Leveraged)</span>
                <span className="text-white font-bold pl-2 text-right">
                  <span className="text-rose-500 font-extrabold">{calculatedVar.toFixed(2)}%</span> Account Cap
                </span>
              </div>

              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Kelly Criterion Size Fraction</span>
                <span className="text-zinc-300 font-extrabold text-right">{spState.kellyFraction}</span>
              </div>

              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Liquidation Slippage Guard</span>
                <span className="text-zinc-300 font-extrabold text-right">{liquidationSpreadPercent}% distance</span>
              </div>

              <div className="flex justify-between items-center py-2">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Max Margin Threshold Clearance</span>
                <span className="text-[#10b981] font-extrabold text-right">{calculatedMarginThreshold}% Equity</span>
              </div>
            </div>

            {/* Horizontal Gauge Bar */}
            <div className="pt-2 space-y-1.5">
              <div className="flex justify-between text-[9px] font-mono text-zinc-500 uppercase font-black">
                <span>Safe Safeguard</span>
                <span className="text-rose-500 font-bold uppercase">Critical Bounds reached</span>
              </div>
              <div className="h-2 bg-zinc-950 rounded-full overflow-hidden border border-zinc-900 p-[1px]">
                <div 
                  className={`h-full rounded-full transition-all duration-300 ${
                    leverage < 50 
                      ? 'bg-emerald-500' 
                      : leverage < 150 
                        ? 'bg-sky-500' 
                        : leverage < 300 
                          ? 'bg-yellow-500' 
                          : 'bg-rose-500 animate-pulse'
                  }`}
                  style={{ width: `${Math.min(100, (leverage / 500) * 100)}%` }}
                />
              </div>
            </div>

            {/* Immersive Stress Event Projection Matrix */}
            <div className="mt-2.5 p-3.5 bg-black/50 border border-zinc-800 rounded-lg space-y-3 font-mono">
              <span className="text-[10px] font-bold text-rose-500 uppercase tracking-widest block border-b border-zinc-900 pb-1.5">
                Stress Assessment Model
              </span>
              
              <div className="space-y-2 text-[10px] text-zinc-400">
                <div className="flex justify-between border-b border-zinc-900 pb-1">
                  <span>Black Swan (Flash Depeg):</span> 
                  <strong className={leverage > 100 ? "text-rose-500 font-bold" : "text-emerald-400"}>
                    {leverage > 100 ? "Force Liquidation Alert" : "Mitigated via Reserves"}
                  </strong>
                </div>
                
                <div className="flex justify-between border-b border-zinc-900 pb-1">
                  <span>HFT Liquidity Freeze:</span> 
                  <strong className="text-zinc-300">
                    Slippage: {((leverage * 0.005) + 0.1).toFixed(2)} bps
                  </strong>
                </div>

                <div className="flex justify-between font-medium">
                  <span>Interest Rate Shock (50bps):</span>
                  <strong className={profile.riskAppetite === 'Conservative' ? 'text-emerald-400' : 'text-yellow-400'}>
                    {profile.riskAppetite === 'Conservative' ? 'Income Neutral' : 'Delta Shift Imbalance'}
                  </strong>
                </div>
              </div>
            </div>

          </div>

        </div>
      </div>
    )}

      {activeTab === 'billing' && (
        <div className="space-y-6">
          
          {/* Top Token Telemetry Panels */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            <div className="p-4 bg-zinc-900/30 border border-zinc-850 rounded-xl flex items-center justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-[#e11d48]/10 to-transparent" />
              <div>
                <span className="text-[10px] font-mono text-zinc-500 uppercase font-extrabold tracking-wide block">Usage Credits Ledger</span>
                <p className="text-3xl font-mono text-white font-bold mt-1 tracking-tight">{credits.toFixed(2)} PRIV</p>
                <div className="flex items-center gap-1.5 mt-1 font-mono text-[9px] text-[#10b981]">
                  <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                  <span>1 PRIV = 1 Autonomous Run</span>
                </div>
              </div>
              <button 
                onClick={handleRefreshCredits}
                className="p-2 border border-zinc-850 hover:border-zinc-700 bg-zinc-950 text-zinc-400 hover:text-white rounded-lg transition"
                title="Synchronize direct balance"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 bg-zinc-900/30 border border-zinc-850 rounded-xl flex items-center justify-between font-mono">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase font-extrabold tracking-wide">License Level</span>
                <p className="text-base font-serif italic text-rose-400 font-bold mt-1">
                  {nodeTier === 'standard' ? 'SANS Standard Allocation' : nodeTier === 'obsidian' ? 'SANS Obsidian Elite' : 'Sovereign Institutional'}
                </p>
                <span className="text-[9px] text-zinc-400 uppercase font-medium mt-0.5 block">
                  LAG LIMIT: <strong className="text-white">{nodeTier === 'standard' ? '0.003s' : nodeTier === 'obsidian' ? '0.0008s' : '0.0003s'}</strong>
                </span>
              </div>
              <Cpu className="w-8 h-8 text-rose-500/10" />
            </div>

            <div className="p-4 bg-zinc-900/30 border border-zinc-850 rounded-xl flex items-center justify-between font-mono">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase font-extrabold tracking-wide">Live Pilot Node</span>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`px-2 py-0.5 text-[8px] rounded border uppercase font-extrabold font-mono tracking-widest ${
                    isPilotRunning 
                      ? 'bg-emerald-950/40 text-emerald-400 border-emerald-900/50 animate-pulse' 
                      : 'bg-zinc-950 text-zinc-500 border-zinc-900'
                  }`}>
                    {isPilotRunning ? 'Active Execution' : 'Standby Mode'}
                  </span>
                </div>
                <p className="text-[9px] text-zinc-500 mt-1.5 uppercase">Node 04 Server: Europe-West-2</p>
              </div>
              <Coins className="w-8 h-8 text-rose-500/10" />
            </div>

          </div>

          {/* Interactive Multi-Node Licensing & Sponsor Topups Section */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

            {/* License Switcher Card */}
            <div className="xl:col-span-1 bg-zinc-950/40 p-5 border border-zinc-850 rounded-xl space-y-4">
              <h3 className="text-xs font-mono uppercase tracking-widest font-extrabold text-white border-b border-zinc-900 pb-2 flex items-center gap-1.5">
                <Landmark className="w-4 h-4 text-rose-500" /> SANS Node Licenses
              </h3>
              <p className="text-[11px] font-sans text-zinc-400 leading-relaxed font-light">
                Upgrade your allocated execution queue inside the SANS network matrix to reduce front-end execution delays.
              </p>

              <div className="space-y-3.5 pt-1">
                {[
                  { id: 'standard', name: 'Standard Allocation', cost: '$75/mo', limit: '250 PRIV Credits', speed: '0.003s Delay', border: 'border-zinc-900' },
                  { id: 'obsidian', name: 'SANS Obsidian Elite', cost: '$150/mo', limit: '500 PRIV Credits', speed: '0.0008s Priority queue', border: 'border-rose-900/40' },
                  { id: 'sovereign', name: 'Institutional Cluster', cost: '$300/mo', limit: '1200 PRIV Credits', speed: '0.0003s Subatomic sweeps', border: 'border-amber-900/40' }
                ].map(item => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setNodeTier(item.id as any);
                      if (item.id === 'standard') handleRefreshCredits();
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      nodeTier === item.id 
                        ? 'bg-rose-950/15 border-rose-500/40 shadow-[0_0_8px_rgba(225,29,72,0.15)]' 
                        : 'bg-zinc-900/40 border-zinc-900 hover:bg-zinc-900 hover:border-zinc-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-white uppercase">{item.name}</span>
                      <span className="text-xs font-mono font-bold text-rose-400">{item.cost}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mt-1.5 font-medium">
                      <span>{item.limit}</span>
                      <span className="text-[#10b981]">{item.speed}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Pilot Gas Burner & Sponsor Module */}
            <div className="xl:col-span-2 bg-zinc-950/40 p-5 border border-zinc-850 rounded-xl space-y-4">
              
              <div className="border-b border-zinc-900 pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-xs font-mono uppercase tracking-widest font-extrabold text-white flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-[#e11d48]" /> Interactive Node Gas Burner
                </h3>
                
                {/* Burner Toggle Control */}
                <button
                  onClick={() => setIsPilotRunning(!isPilotRunning)}
                  className={`px-3 py-1 text-[10px] font-mono font-bold uppercase border rounded-lg flex items-center gap-1.5 cursor-pointer transition ${
                    isPilotRunning 
                      ? 'bg-rose-950 text-rose-400 border-rose-800 hover:bg-rose-900' 
                      : 'bg-[#10b981]/10 text-emerald-400 border-emerald-900 hover:bg-[#10b981]/20'
                  }`}
                  id="btn-pilot-simulation"
                >
                  {isPilotRunning ? (
                    <>
                      <Pause className="w-3 h-3 text-rose-500 animate-spin" />
                      <span>PAUSE PILOT RUNS</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3 text-emerald-400" />
                      <span>ACTIVATE PILOT EXECUTION</span>
                    </>
                  )}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Left Mini Module: Token Booster Sponsor */}
                <div className="space-y-3 bg-black/40 p-4 rounded-lg border border-zinc-900">
                  <span className="text-[10px] font-bold text-[#e11d48] uppercase tracking-wider block font-mono">
                    Node Token Sponsorship Portal
                  </span>
                  <p className="text-[11px] font-sans text-zinc-400 leading-snug font-light">
                    Select a block allocation value to instantly sponsor Node 04 operational costs and mint credits.
                  </p>
                  
                  <div className="grid grid-cols-3 gap-2 pt-1">
                    {[
                      { amount: 100, label: '+100 PRIV' },
                      { amount: 250, label: '+250 PRIV' },
                      { amount: 600, label: '+600 PRIV' }
                    ].map((btn, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSponsorBoost(btn.amount)}
                        className="p-2 bg-zinc-900 hover:bg-[#e11d48]/10 hover:text-rose-400 hover:border-rose-500/30 border border-zinc-800 text-[10px] font-mono font-black rounded-md text-zinc-300 transition uppercase cursor-pointer"
                        id={`btn-sponsor-${btn.amount}`}
                      >
                        {btn.label}
                      </button>
                    ))}
                  </div>

                  <div className="border-t border-zinc-900/60 pt-2 flex justify-between font-mono text-[9px] text-zinc-500 uppercase">
                    <span>MINT RATE: STABLE</span>
                    <span>SLIPPAGE ZERO GATED</span>
                  </div>
                </div>

                {/* Right: Live Credit Operation Streams logs */}
                <div className="space-y-2 flex flex-col justify-between">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest block font-mono">
                    Node Operation Telemetry
                  </span>
                  
                  <div className="flex-1 max-h-[110px] overflow-y-auto space-y-1.5 scrollbar-hide pr-1">
                    {liveLogQueue.slice(0, 4).map((log, lIdx) => (
                      <div 
                        key={log.id} 
                        className="flex items-center justify-between text-[10px] font-mono p-1 bg-zinc-950/60 border border-zinc-900/30 rounded"
                      >
                        <div className="truncate pr-4 text-zinc-400 flex items-center gap-1">
                          <span className="text-zinc-650 font-black">{log.id}</span>
                          <span className="truncate">{log.action}</span>
                        </div>
                        <span className={`font-black flex-shrink-0 ${log.type === 'burn' ? 'text-rose-500' : log.type === 'mint' ? 'text-emerald-400' : 'text-zinc-500'}`}>
                          {log.impact}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>

            </div>

          </div>

          {/* SANS Ledger Accounts List / Past Billing Invoices */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-widest font-extrabold text-white flex items-center justify-between">
              <span>Sovereign Ledger Billing Entries</span>
              <span className="text-[9px] font-extralight text-zinc-500 capitalize font-sans">Hash #948294</span>
            </h3>
            
            <div className="overflow-x-auto border border-zinc-900 rounded-xl bg-zinc-950/20">
              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="bg-zinc-950 border-b border-zinc-900 text-zinc-500 font-semibold text-[10px] uppercase tracking-wider">
                    <th className="p-3">Reference Hash</th>
                    <th className="p-3">Dossier Date</th>
                    <th className="p-3">Reference / Plan</th>
                    <th className="p-3">Sovereign Allocation</th>
                    <th className="p-3 text-right">Amount</th>
                    <th className="p-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="border-b border-zinc-900/50 hover:bg-zinc-900/20 transition">
                      <td className="p-3 text-zinc-400 font-bold">{inv.id}</td>
                      <td className="p-3 text-zinc-500">{inv.date}</td>
                      <td className="p-3 text-zinc-200">{inv.tier}</td>
                      <td className="p-3 text-emerald-400 font-bold">{inv.creditsAdded}</td>
                      <td className="p-3 text-right text-zinc-300">{inv.amount}</td>
                      <td className="p-3 text-right">
                        <span className="p-1 px-2.5 bg-emerald-950/35 text-emerald-400 border border-emerald-900/30 rounded text-[10px] font-bold uppercase">
                          {inv.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}

      {activeTab === 'brokers' && (
        <div className="space-y-4">
          <div className="p-5 border border-zinc-800 bg-zinc-950/40 rounded-xl">
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-widest">
              Deriv broker connection
            </h3>
            <p className="text-[11px] text-zinc-400 font-mono mt-1 mb-4 leading-relaxed">
              Link your Deriv account (demo works too) so live prices, positions
              and execution light up across the terminal. Demo mode uses your
              real Deriv demo account once linked.
            </p>
            <DerivConnectCard />
          </div>
        </div>
      )}

      {activeTab === 'kyc' && (
        <div className="space-y-4">
          {kycStatus === 'approved' ? (
            <div className="p-8 text-center border border-emerald-900/30 bg-emerald-950/15 rounded-xl space-y-4">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto animate-bounce" id="kyc-approved-badge" />
              <div>
                <h3 className="text-lg font-serif italic text-white font-normal">SANS KYC APPROVED & LINKED</h3>
                <p className="text-xs text-zinc-400 font-mono mt-1.5 max-w-md mx-auto">
                  Your legal compliance status is fully approved and locked on the SANS Distributed Ledger. Active real-time indicators and live trade execution modules are available.
                </p>
                <div className="inline-block mt-4 p-2 px-4 bg-emerald-950/40 text-emerald-400 font-mono text-[10px] uppercase font-bold border border-emerald-900/30 rounded-lg">
                  COMPLIANT: SOVEREIGN TRADE ALLOCATIONS GRANTED
                </div>
              </div>
            </div>
          ) : kycStatus === 'submitted' || kycStatus === 'pending' ? (
            <div className="p-8 text-center border border-zinc-800 bg-zinc-950/40 rounded-xl space-y-4">
              <div className="w-12 h-12 rounded-full border-2 border-rose-500/20 border-t-rose-500 animate-spin mx-auto" />
              <div>
                <h3 className="text-lg font-serif italic text-white font-normal">AML DOSSIER IN REVIEW</h3>
                <p className="text-xs text-zinc-400 font-mono mt-1.5 max-w-sm mx-auto">
                  Dossier received and queued for compliance review — biometric,
                  address, and blacklist checks run in that order. A copy was
                  emailed to our compliance desk for the human review step.
                </p>
                {(() => {
                  let ref = "";
                  let when = "";
                  try {
                    ref = localStorage.getItem("xm_kyc_ref") || "";
                    const ts = localStorage.getItem("xm_kyc_submitted_at") || "";
                    if (ts) when = new Date(ts).toLocaleString();
                  } catch (_) {}
                  if (!ref && !when) return null;
                  return (
                    <p className="text-[11px] text-zinc-500 font-mono mt-2">
                      {ref ? <>Ref: <span className="text-zinc-200">{ref}</span></> : null}
                      {ref && when ? " · " : null}
                      {when ? <>submitted {when}</> : null}
                    </p>
                  );
                })()}
                <div className="inline-block mt-4 p-2 px-4 bg-rose-950/30 text-rose-400 font-mono text-[9px] uppercase font-bold border border-rose-500/20 rounded-lg animate-pulse">
                  Ledger status: Pending Queue Handshake
                </div>
              </div>
            </div>
          ) : kycStatus === 'rejected' ? (
            <div className="p-8 text-center border border-rose-900/30 bg-rose-950/10 rounded-xl space-y-4">
              <span className="inline-block w-12 h-12 text-4xl text-rose-500">&#9888;</span>
              <div>
                <h3 className="text-lg font-serif italic text-white flex items-center justify-center gap-1.5 text-rose-400 font-normal">APPLICATION SUSPENDED</h3>
                <p className="text-xs text-zinc-400 font-mono mt-1.5 max-w-sm mx-auto">
                  Your application did not comply with default risk restrictions. Please review the internal comments or contact a SANS compliance representative.
                </p>
                <button
                  onClick={() => setKycStatus("draft")}
                  className="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs font-bold rounded-lg transition"
                >
                  Edit and Resubmit Application
                </button>
              </div>
            </div>
          ) : (
            <KycVerificationPage demoMode={demoMode} onSuccess={() => setKycStatus('submitted')} />
          )}
        </div>
      )}

    </div>
  );
}
