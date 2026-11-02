import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import KycVerificationPage from './KycVerificationPage';
import DerivConnectCard from '../DerivConnectCard';
import TradingViewCard from '../TradingViewCard';
import MT5BridgeCard from '../MT5BridgeCard';
import { TaxIntelligence } from '../TaxIntelligence';
import apiClient from '../../api/apiClient';
import ContactVerifier, { VerifiedEntry } from './ContactVerifier';
import { 
  User, 
  Shield,
  Link2,
  Landmark, 
  ExternalLink, 
  CheckCircle2
} from 'lucide-react';

interface UserProfileEditorProps {
}

export default function UserProfileEditor() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'profile' | 'kyc' | 'brokers' | 'tax'>('profile');
  const [hasRealConnection, setHasRealConnection] = useState<boolean>(false);
  // Broker connections beyond Deriv (TradingView / MT5 bridge / affiliate
  // venues) are reserved for the two highest subscription tiers --
  // sovereign + autonomous -- plus admins. Server-derived tier only
  // (GET /subscriptions/me -> tier), never the cosmetic node-tier picker.
  const [brokerTierOk, setBrokerTierOk] = useState(false);
  // Identity Registry KYC is the source of truth for legal names. The
  // First/Last Legal Name inputs are read-only and mirror the KYC record
  // (null = record not loaded yet). Edit surface: Profile -> Identity
  // Verification (KYC form); a submitted KYC only changes via amendment.
  const [kycNames, setKycNames] = useState<{ first: string; last: string } | null>(null);
  const [signalBrokers, setSignalBrokers] = useState<any[]>([]);
  
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
    // Tax Intelligence lives here now (moved from the sidebar); the old
    // /dashboard/tax route redirects to ?tab=tax.
    if (params.get("tab") === "tax") {
      setActiveTab("tax");
    }
  }, [location]);
  
  // Profile Parameters
  const [profile, setProfile] = useState(() => {
    const saved = localStorage.getItem("xm_user_profile");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Saved profiles written by older builds (or a partially-failed
        // hydrate) can miss fields entirely; a missing email/phone used
        // to reach <ContactVerifier contact={profile.email}> and crash
        // the whole page on `undefined.trim()`. Merge over the empty
        // shell so every field is always a string.
        return {
          firstName: '',
          lastName: '',
          email: '',
          phone: '',
          country: '',
          experience: '< 1 year',
          riskAppetite: 'Moderate',
          tradingGoal: '',
          ...parsed,
          ...(typeof parsed?.email === 'string' ? {} : { email: '' }),
          ...(typeof parsed?.phone === 'string' ? {} : { phone: '' }),
        };
      } catch (_) {}
    }
    // FIX: this used to fall back to a fabricated identity (name
    // "Alistair Sterling", a South African phone number) that every
    // user without a saved profile yet would see -- indistinguishable
    // from a real person's details being shown on someone else's
    // account. LoginGate.tsx now prefills real Auth0 profile data
    // (given_name/family_name/email/picture) into xm_user_profile right
    // after login, so this fallback should rarely even be reached; when
    // it is (e.g. this component rendering before that prefill runs),
    // it must show an empty shell for the user to fill in themselves,
    // never someone else's -- or a fictional -- identity.
    return {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      country: '',
      experience: '< 1 year',
      riskAppetite: 'Moderate',
      tradingGoal: ''
    };
  });

  // Leverage & Custom Calibration Slider
  const [leverage, setLeverage] = useState<number>(() => {
    return parseInt(localStorage.getItem("xm_profile_leverage") || "20");
  });

  // KYC Status Sync
  const [kycStatus, setKycStatus] = useState<string>(() => {
    return localStorage.getItem("xm_kyc_status") || "unsubmitted";
  });

  // Tier gate for the broker-connections block (sovereign/autonomous or
  // admin). Both probes are console-clean when signed out: whoami is
  // anon-safe and getMySubscription short-circuits without a request.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let ok = false;
      try {
        const res: any = await apiClient.get('/api/v1/admin/whoami');
        ok = !!res?.data?.data?.admin;
      } catch (_) {
        /* stay non-admin */
      }
      if (!ok) {
        try {
          const body: any = await apiClient.getMySubscription();
          const sub = body?.subscription ?? (body && typeof body === 'object' ? body : null);
          const tier = sub?.tier;
          ok = tier === 'sovereign' || tier === 'autonomous';
        } catch (_) {
          /* signed out / free..elite -> no extra broker block */
        }
      }
      if (!cancelled) setBrokerTierOk(ok);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Affiliate venue directory (XM/IFX/FBS) -- only fetched once the
  // block is actually going to render.
  useEffect(() => {
    if (!brokerTierOk) return;
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.getSignalBrokers();
        const d = res?.data?.data ?? res?.data ?? {};
        if (!cancelled) setSignalBrokers(d.brokers || []);
      } catch (_) {
        /* offline: block still renders with the two cards */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [brokerTierOk]);

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

  // Sync state modifications
  useEffect(() => {
    localStorage.setItem("xm_user_profile", JSON.stringify(profile));
    localStorage.setItem("xm_account_email", profile.email);
    localStorage.setItem("xm_user_risk_appetite", profile.riskAppetite);
  }, [profile]);

  useEffect(() => {
    localStorage.setItem("xm_profile_leverage", leverage.toString());
  }, [leverage]);

  // ── Server-side persistence ─────────────────────────────────────────
  // The account row on the server is the source of truth; localStorage
  // above is only a fast-paint cache. Without this, everything a user
  // entered lived in one browser and vanished on any other device.
  const [verifiedList, setVerifiedList] = useState<VerifiedEntry[]>([]);
  const [emailLocked, setEmailLocked] = useState(false);
  const [serverHydrated, setServerHydrated] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileError, setProfileError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let hydrated = false;
    const loadIdentity = async () => {
      try {
        const [meRes, verRes, kycRes]: any[] = await Promise.all([
          apiClient.getMyProfile(),
          apiClient.getVerifiedContacts().catch(() => null),
          apiClient.getKycRecord().catch(() => null),
        ]);
        const d = meRes?.data?.data ?? meRes?.data;
        if (cancelled || !d) return;

        const vd = verRes?.data?.data ?? verRes?.data ?? {};
        setVerifiedList(vd.verified || []);
        setEmailLocked(!!d.email);

        const nothingOnServer =
          !d.phone && !d.country && !d.experience && !d.trading_goal &&
          !d.risk_appetite && d.leverage == null;

        if (nothingOnServer) {
          // First visit since server-side storage shipped: push whatever
          // this browser already holds up to the account (once), so
          // existing users don't lose what they entered before.
          const hasLocal = profile.phone || profile.country || profile.tradingGoal;
          if (hasLocal) {
            try {
              await apiClient.updateMyProfile({
                phone: profile.phone || undefined,
                country: profile.country || undefined,
                experience: profile.experience || undefined,
                trading_goal: profile.tradingGoal || undefined,
                risk_appetite: profile.riskAppetite || undefined,
                leverage,
              });
            } catch (_) {
              /* keep local; will retry on next Save */
            }
          }
        } else {
          setProfile((prev: any) => ({
            ...prev,
            firstName: d.given_name ?? prev.firstName,
            lastName: d.family_name ?? prev.lastName,
            email: d.email ?? prev.email,
            phone: d.phone ?? prev.phone,
            country: d.country ?? prev.country,
            experience: d.experience ?? prev.experience,
            tradingGoal: d.trading_goal ?? prev.tradingGoal,
            riskAppetite: d.risk_appetite ?? prev.riskAppetite,
          }));
          if (d.leverage != null) setLeverage(d.leverage);
        }
        // Name/email always come from the account when present, even on
        // the very first visit (LoginGate prefills them from the login).
        if (nothingOnServer) {
          setProfile((prev: any) => ({
            ...prev,
            firstName: d.given_name ?? prev.firstName,
            lastName: d.family_name ?? prev.lastName,
            email: d.email ?? prev.email,
          }));
        }
        // Identity Registry KYC owns the legal names: overlay whatever the
        // KYC record holds, and strip email-shaped junk some profiles carry
        // (an account email previously landed in First Legal Name).
        const kd: any = kycRes ?? {};
        const kycPersonal: any = kd.personal ?? kd?.data?.personal ?? {};
        const kycFirst = String(kycPersonal.legal_first_name || "").trim();
        const kycLast = String(kycPersonal.legal_last_name || "").trim();
        setProfile((prev: any) => {
          const isEmail = (v: any) => /\S+@\S+/.test(String(v || ""));
          let firstName = isEmail(prev.firstName) ? "" : prev.firstName;
          let lastName = isEmail(prev.lastName) ? "" : prev.lastName;
          if (kycFirst) firstName = kycFirst;
          if (kycLast) lastName = kycLast;
          if (firstName === prev.firstName && lastName === prev.lastName) return prev;
          return { ...prev, firstName, lastName };
        });
        if (kycRes !== null && kycRes !== undefined) {
          setKycNames({ first: kycFirst, last: kycLast });
        }
        setServerHydrated(true);
        hydrated = true;
      } catch (_) {
        /* offline / unauthenticated: stay on the local cache */
      }
    };
    loadIdentity();
    // Auth0 registers its token getter only in LoginGate's effect, which
    // runs AFTER children mount -- so the first loadIdentity often runs
    // tokenless (verified-only endpoints answer 401, no request fires).
    // Re-run when the getter lands so the server copy still hydrates.
    const onAuthReady = () => {
      if (!hydrated && !cancelled) loadIdentity();
    };
    window.addEventListener("priv:auth-ready", onAuthReady);
    return () => {
      cancelled = true;
      window.removeEventListener("priv:auth-ready", onAuthReady);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Legal names mirror Identity Registry KYC live: re-read the record
  // whenever we come back from the Identity Verification tab (draft KYC
  // edits land there first), so the locked fields never go stale.
  useEffect(() => {
    if (activeTab !== "profile" || !serverHydrated) return;
    let dead = false;
    apiClient
      .getKycRecord()
      .then((kd: any) => {
        if (dead || !kd) return;
        const p = kd.personal ?? {};
        const first = String(p.legal_first_name || "").trim();
        const last = String(p.legal_last_name || "").trim();
        setKycNames({ first, last });
        setProfile((prev: any) => {
          const nf = first || prev.firstName;
          const nl = last || prev.lastName;
          if (nf === prev.firstName && nl === prev.lastName) return prev;
          return { ...prev, firstName: nf, lastName: nl };
        });
      })
      .catch(() => {
        /* keep whatever we already mirrored */
      });
    return () => {
      dead = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, serverHydrated]);

  // Leverage slider is changed outside the form, so persist it
  // (debounced) once we've loaded the server copy -- never before, or a
  // default value could overwrite what's stored on the account.
  useEffect(() => {
    if (!serverHydrated) return;
    const t = window.setTimeout(() => {
      apiClient.updateMyProfile({ leverage }).catch(() => {});
    }, 800);
    return () => window.clearTimeout(t);
  }, [leverage, serverHydrated]);

  // Real-time synchronization
  useEffect(() => {
    const handleStatusSync = () => {
      const liveStatus = localStorage.getItem("xm_kyc_status") || "unsubmitted";
      setKycStatus(liveStatus);
    };
    const interval = setInterval(handleStatusSync, 900);
    return () => clearInterval(interval);
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    // Local cache first (instant UI), then the account on the server --
    // the server write is what makes this survive a device change.
    localStorage.setItem("xm_user_profile", JSON.stringify(profile));
    localStorage.setItem("xm_user_risk_appetite", profile.riskAppetite);
    window.dispatchEvent(new Event('storage'));

    setProfileSaving(true);
    setProfileError("");
    setProfileSuccessMessage("");
    try {
      await apiClient.updateMyProfile({
        given_name: profile.firstName,
        family_name: profile.lastName,
        phone: profile.phone,
        country: profile.country,
        experience: profile.experience,
        trading_goal: profile.tradingGoal,
        risk_appetite: profile.riskAppetite,
        leverage,
        // Only sent when the account has no email yet (e.g. Twitter login).
        ...(!emailLocked && profile.email ? { email: profile.email } : {}),
      });
      if (!emailLocked && profile.email) setEmailLocked(true);
      setProfileSuccessMessage("Profile saved to your account. It will be here on any device you sign in from.");
      setTimeout(() => setProfileSuccessMessage(""), 4000);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setProfileError(
        typeof detail === "string"
          ? detail
          : detail?.message || err?.message || "Could not save your profile. Please try again."
      );
    } finally {
      setProfileSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Mini tabs header resembling a trading desktop toolbar */}
      <div className="flex border-b border-zinc-900 pb-3 gap-2 overflow-x-auto scrollbar-hide">
        {[
          { id: 'profile', label: 'Sovereign Profile', icon: User },
          { id: 'brokers', label: 'Broker Connections', icon: Link2 },
          { id: 'kyc', label: 'Identity Registry KYC', icon: Shield },
          { id: 'tax', label: 'Tax Intelligence', icon: Landmark }
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

      {activeTab === 'tax' && (
        <div className="space-y-4">
          <TaxIntelligence />
        </div>
      )}

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
                    readOnly
                    tabIndex={-1}
                    aria-readonly="true"
                    className="w-full p-2.5 bg-zinc-900/60 text-zinc-300 rounded border border-zinc-800 font-mono text-xs opacity-70 cursor-not-allowed"
                  />
                  <p className="mt-1 text-[9px] font-mono text-zinc-500">
                    {kycNames && (kycNames.first || kycNames.last)
                      ? "From Identity Registry KYC — source of truth. Changes via Identity Verification."
                      : kycNames
                        ? "Not set in Identity Registry KYC yet — add it under Identity Verification."
                        : "Loading from Identity Registry KYC…"}
                  </p>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Last Legal Name</label>
                  <input 
                    type="text" 
                    value={profile.lastName} 
                    id="profile-lastName"
                    readOnly
                    tabIndex={-1}
                    aria-readonly="true"
                    className="w-full p-2.5 bg-zinc-900/60 text-zinc-300 rounded border border-zinc-800 font-mono text-xs opacity-70 cursor-not-allowed"
                  />
                  <p className="mt-1 text-[9px] font-mono text-zinc-500">
                    Mirrors Identity Registry KYC — never edited here.
                  </p>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Identity verification Email</label>
                  <input 
                    type="email" 
                    value={profile.email} 
                    id="profile-email"
                    readOnly={emailLocked}
                    onChange={e => setProfile({...profile, email: e.target.value})}
                    className={`w-full p-2.5 bg-zinc-950/80 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition ${emailLocked ? 'opacity-70 cursor-not-allowed' : ''}`}
                  />
                  {emailLocked && (
                    <p className="mt-1 text-[9px] font-mono text-zinc-500">Tied to your login and can't be changed here.</p>
                  )}
                  <ContactVerifier kind="email" contact={profile.email} verified={verifiedList} onVerified={setVerifiedList} />
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-zinc-400 uppercase font-extrabold tracking-widest mb-1.5">Handshake Phone Range</label>
                  <input 
                    type="text" 
                    value={profile.phone} 
                    id="profile-phone"
                    onChange={e => setProfile({...profile, phone: e.target.value})}
                    placeholder="+27 82 000 0000"
                    className="w-full p-2.5 bg-zinc-955 text-white rounded border border-zinc-800 font-mono text-xs focus:outline-none focus:border-rose-500 transition"
                  />
                  <ContactVerifier kind="phone" contact={profile.phone} verified={verifiedList} onVerified={setVerifiedList} />
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

              {profileError && (
                <div className="text-[10px] font-mono text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded px-3 py-2">
                  {profileError}
                </div>
              )}
              {profileSuccessMessage && (
                <div className="text-[10px] font-mono text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded px-3 py-2">
                  {profileSuccessMessage}
                </div>
              )}

              <div className="flex justify-between items-center pt-3 text-right">
                <p className="text-[9px] font-mono text-zinc-500 leading-snug text-left max-w-sm">
                  * Synchronizing this deck auto-adjusts systemic leverage factors across the Broker Terminal and limits trade sizing margins.
                </p>
                <button 
                  type="submit"
                  id="btn-sync-profile"
                  disabled={profileSaving}
                  className="px-5 py-2.5 bg-gradient-to-r from-rose-700 to-rose-600 hover:from-rose-600 hover:to-rose-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-mono text-xs font-bold rounded-lg transition-all shadow-[0_4px_12px_rgba(225,29,72,0.15)] cursor-pointer"
                >
                  {profileSaving ? "Syncing…" : "Sync Systemic Risk Constraints"}
                </button>
              </div>
            </form>
          </div>

          {/* Risk settings summary — echoes only what you actually saved;
              no invented grades, VaR, Kelly or stress numbers. */}
          <div className="p-5 border border-zinc-800/80 rounded-xl bg-zinc-950/40">
            <h3 className="text-xs font-mono uppercase tracking-widest font-extrabold text-zinc-400 border-b border-zinc-900 pb-2 mb-3">
              Your Risk Settings
            </h3>
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Risk Appetite</span>
                <span className="text-white font-bold">{profile.riskAppetite || "—"}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-zinc-900">
                <span className="text-zinc-500 font-bold text-[10px] uppercase">Leverage</span>
                <span className="text-white font-bold">{leverage}x</span>
              </div>
              <p className="text-[11px] text-zinc-500 leading-relaxed pt-1">
                These values shape how the autotrader sizes positions on your
                connected account. They are saved to your profile — nothing on
                this panel is simulated or projected.
              </p>
            </div>
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

          {brokerTierOk && (
            <div className="p-5 border border-zinc-800 bg-zinc-950/40 rounded-xl space-y-4">
              <div>
                <h3 className="text-sm font-mono font-bold text-white uppercase tracking-widest">
                  Broker connections
                </h3>
                <p className="text-[11px] text-zinc-400 font-mono mt-1 leading-relaxed">
                  Additional execution venues — available on the two highest tiers
                  (Sovereign and Autonomous). The MT5 bridge pairing itself is
                  reserved for Autonomous subscribers.
                </p>
              </div>
              <TradingViewCard />
              <MT5BridgeCard />
              {signalBrokers
                .filter((b) => b.id !== 'deriv')
                .map((b) => (
                  <div
                    key={b.id}
                    className="flex items-center justify-between gap-3 p-3 rounded-lg border border-white/10 bg-black/40"
                  >
                    <div className="min-w-0">
                      <div className="text-sm text-white font-semibold">{b.name}</div>
                      {b.description && (
                        <div className="text-[11px] text-zinc-400 font-mono mt-0.5">
                          {b.description}
                        </div>
                      )}
                    </div>
                    {b.url && (
                      <a
                        href={b.url}
                        target="_blank"
                        rel="noreferrer"
                        className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition"
                      >
                        Open account <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                ))}
            </div>
          )}
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
            <KycVerificationPage onSuccess={() => setKycStatus('submitted')} />
          )}
        </div>
      )}

    </div>
  );
}
