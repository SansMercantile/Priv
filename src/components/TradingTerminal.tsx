import React, { useState, useEffect, useRef } from "react";
import { useAutotrader } from "./terminal/useAutotrader";
import { useDerivSymbols, tvSymbolFor } from "./terminal/derivSymbols";
import SymbolPicker from "./terminal/SymbolPicker";
import NativeChart from "./terminal/NativeChart";
import { getAppUserId } from "../lib/appUserId";
import {
  Activity,
  Wifi,
  WifiOff,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  X,
  Calculator,
  Maximize2,
  Bot,
  Lock,
  Sparkles,
} from "lucide-react";

// Rise & Fall mini app (Deriv "Priv Core mini" app id 34vzk..., served
// as-is from its own Vercel project; its OAuth redirect URI is pinned to
// this exact host, so it must be framed from this URL, never rewritten).
const RISE_FALL_MINI_APP_URL = "https://privcoremini.sansmercantile.com";

// ── Real broker constant ─────────────────────────────────────────────────
// Default desk connection. At runtime this is replaced by the user's own
// Trading terminal resolves its broker from the signed-in user's linked
// Deriv account for the current demo toggle position (their per-type
// account via /deriv/active-account). Null when the mode has nothing
// linked -- the UI prompts to connect instead of showing any shared or
// other-mode account.

import { getAuthToken } from "../lib/authToken";
import { Link } from "react-router-dom";
import apiClient from "../api/apiClient";

// Authenticated headers for every backend call: the verified Bearer
// token (when signed in) plus the browser id. The old version sent
// X-User-Id only, so every call resolved the anonymous key -- whose
// records were claimed away at login -- and the terminal fell back to
// the shared desk (a LIVE account) in every mode, including demo.
async function userHeader(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  try {
    headers["X-User-Id"] = getAppUserId();
  } catch (_) {
    /* ignore */
  }
  try {
    const token = await getAuthToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  } catch (_) {
    /* ignore */
  }
  return headers;
}

interface OpenPosition {
  order_id: string;
  symbol: string | null;
  contract_type: string;
  buy_price: number;
  payout: number;
  purchase_time: number;
  date_expiry: number;
  longcode: string;
}

interface AccountInfo {
  account_id: string;
  balance: number;
  currency: string;
  account_type: string;
}

interface AutonomousAnalysis {
  reasoning: string;
  action: string;
  confidence: number;
  stopLoss: number;
  takeProfit: number;
  lotSize: number;
  rationale: string;
}

// Default symbol only; the full, searchable Deriv universe now comes
// from useDerivSymbols()/SymbolPicker (GET /api/brokers/deriv/symbols) --
// this hardcoded 5-symbol list previously WAS the entire Order Dispatch
// and Signals selector.
const DEFAULT_SYMBOL = "R_100";

// ── Error Boundary — prevents blank screen on any runtime crash ──────────
class TerminalErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: string }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: "" };
  }
  static getDerivedStateFromError(err: Error) {
    return { hasError: true, error: err.message };
  }
  componentDidCatch(err: Error, info: React.ErrorInfo) {
    console.error("[TradingTerminal]", err, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] bg-zinc-950 rounded-xl border border-zinc-800 p-8 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-950/40 border border-rose-800/50 flex items-center justify-center mb-4">
            <span className="text-rose-400 text-xl">⚠</span>
          </div>
          <p className="text-white font-mono text-sm font-bold mb-2">Terminal Error</p>
          <p className="text-zinc-400 font-mono text-xs mb-4 max-w-md">{this.state.error}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: "" })}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white font-mono text-xs rounded-lg border border-zinc-700 transition"
          >
            Reload Terminal
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function TradingTerminalInner() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  // Active Deriv account for the current demo toggle (loginid for display,
  // broker id for all backend calls). Re-resolved on every poll so flipping
  // the demo toggle takes effect live. Null when this mode has no linked
  // account -- the UI shows a link prompt, never the shared desk (which
  // is bound to a live key and must not leak into demo mode).
  const [brokerId, setBrokerId] = useState<string | null>(null);
  const [activeLogin, setActiveLogin] = useState<string | null>(null);
  const [activeMode, setActiveMode] = useState<"demo" | "live">("demo");
  // Rise & Fall mini app: swapped in place of the desk grid so the
  // embedded app gets full terminal width for its own chart + controls.
  const [showMiniApp, setShowMiniApp] = useState(false);
  const [miniAppSrc, setMiniAppSrc] = useState<string>(RISE_FALL_MINI_APP_URL);
  const [miniAppLoading, setMiniAppLoading] = useState(false);

  // ── SANS Autonomous Desk ─────────────────────────────────────────────
  // Tier gate comes from the real subscription (GET /subscriptions/me ->
  // tier, derived server-side), never localStorage -- same rule as
  // Connections.tsx. Admin accounts pass every gate. Sovereign gets the
  // AI analyze/suggest desk without auto-execution; Autonomous (or
  // admin) gets the full agent.
  const [nodeTier, setNodeTier] = useState<string>("free");
  const [isAdmin, setIsAdmin] = useState(false);
  // Server-side autotrader: arms/disarms a backend loop that keeps
  // running after this tab closes, the user logs out, or the laptop
  // sleeps. Replaces the old client-side isAutoTrading/setInterval
  // mechanism, which died the moment the tab did and only ever
  // evaluated the single symbol on Dispatch.
  const autotrader = useAutotrader(userHeader);
  const [scanAllMarkets, setScanAllMarkets] = useState(false);
  const [autoLogs, setAutoLogs] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("priv_auto_logs") || "[]");
    } catch (_) {
      return [];
    }
  });
  const [autoAnalysis, setAutoAnalysis] = useState<AutonomousAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const syncTier = async () => {
      try {
        const res: any = await apiClient.getMySubscription();
        const body = res?.data ?? res;
        const sub = body?.subscription ?? (body && typeof body === "object" ? body : null);
        if (!cancelled) setNodeTier(sub?.tier || "free");
      } catch (_) {
        /* offline/unauthenticated: stay on last known tier (defaults free) */
      }
    };
    syncTier();
    const interval = setInterval(syncTier, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.get("/api/v1/admin/whoami");
        if (!cancelled && res?.data?.data?.admin) setIsAdmin(true);
      } catch (_) {
        /* stay non-admin */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const canAutoExecute = isAdmin || nodeTier === "autonomous";
  const canUseDesk = canAutoExecute || nodeTier === "sovereign";

  const pushAutoLog = (msg: string) => {
    setAutoLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 100));
  };

  useEffect(() => {
    try {
      localStorage.setItem("priv_auto_logs", JSON.stringify(autoLogs.slice(0, 100)));
    } catch (_) {
      /* quota/private-mode: logs stay in memory only */
    }
  }, [autoLogs]);

  // SSO handoff: fetch THIS user's own Deriv session from the backend
  // (verified Bearer required server-side) and pass it to the mini app
  // via the URL hash, so it opens already authorized -- no second Deriv
  // sign-in inside the frame. Falls back to the plain URL (the mini
  // app's own sign-in) when there is no valid connected session.
  const openMiniApp = async () => {
    setMiniAppLoading(true);
    let src = RISE_FALL_MINI_APP_URL;
    try {
      const res = await fetch("/api/v1/auth/deriv/sso", {
        headers: await userHeader(),
      });
      if (res.ok) {
        const body = await res.json().catch(() => null);
        const token = body?.data?.access_token;
        if (token) {
          src =
            `${RISE_FALL_MINI_APP_URL}/#sso=` +
            encodeURIComponent(JSON.stringify({ access_token: token }));
        }
      }
    } catch {
      /* offline/backend hiccup -> plain URL, never block the terminal */
    }
    setMiniAppSrc(src);
    setMiniAppLoading(false);
    setShowMiniApp(true);
  };

  const pushLog = (msg: string) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 100));
  };

  const resolveBroker = async (): Promise<string | null> => {
    let mode: "demo" | "live" = "demo";
    try {
      mode = localStorage.getItem("demoMode") === "false" ? "live" : "demo";
    } catch (_) {
      /* ignore */
    }
    setActiveMode(mode);
    try {
      const res = await fetch(`/api/v1/auth/deriv/active-account?mode=${mode}`, {
        headers: await userHeader(),
      });
      if (res.ok) {
        const body = await res.json();
        const acct = body?.data?.account;
        if (acct?.broker_id) {
          setBrokerId(acct.broker_id);
          setActiveLogin(acct.loginid || null);
          return acct.broker_id as string;
        }
      }
    } catch {
      /* fall through to unlinked state */
    }
    setBrokerId(null);
    setActiveLogin(null);
    return null;
  };

  const fetchStatus = async (bid: string | null) => {
    if (!bid) {
      setIsConnected(false);
      return;
    }
    try {
      const res = await fetch(`/api/brokers/status/${bid}`, { headers: await userHeader() });
      if (res.ok) {
        const data = await res.json();
        setIsConnected(!data.error);
      } else {
        setIsConnected(false);
      }
    } catch {
      setIsConnected(false);
    }
  };

  const fetchAccount = async (bid: string | null) => {
    if (!bid) {
      setAccount(null);
      return;
    }
    try {
      const res = await fetch(`/api/brokers/account/${bid}`, { headers: await userHeader() });
      if (res.ok) {
        const data = await res.json();
        if (!data.error) setAccount(data);
      }
    } catch {}
  };

  const fetchPositions = async (bid: string | null) => {
    if (!bid) {
      setPositions([]);
      return;
    }
    try {
      const res = await fetch(`/api/brokers/positions?broker_id=${bid}`, { headers: await userHeader() });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setPositions(data);
      }
    } catch {}
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const bid = await resolveBroker();
      if (cancelled) return;
      fetchStatus(bid);
      fetchAccount(bid);
      fetchPositions(bid);
    })();
    const interval = setInterval(async () => {
      const bid = await resolveBroker();
      if (cancelled) return;
      fetchAccount(bid);
      fetchPositions(bid);
    }, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const [selectedSymbol, setSelectedSymbol] = useState(DEFAULT_SYMBOL);
  const { symbols: derivSymbols, loading: symbolsLoading, error: symbolsError } = useDerivSymbols(userHeader);
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");
  const [stake, setStake] = useState<number>(10);
  const [duration, setDuration] = useState<number>(5);
  const [riskPct, setRiskPct] = useState<number>(1);
  const [placingOrder, setPlacingOrder] = useState(false);

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!brokerId) {
      pushLog(`No Deriv ${activeMode} account linked — connect one first.`);
      return;
    }
    if (!isConnected) {
      pushLog("Cannot place order - Deriv connection is offline.");
      return;
    }
    if (stake <= 0) {
      pushLog("Stake must be greater than 0.");
      return;
    }
    setPlacingOrder(true);
    try {
      const res = await fetch("/api/brokers/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(await userHeader()) },
        body: JSON.stringify({
          broker_id: brokerId,
          order_type: orderSide,
          symbol: selectedSymbol,
          volume: stake,
          duration,
          duration_unit: "m",
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        pushLog(
          `Order placed: ${orderSide} ${selectedSymbol}, stake ${stake} ${account?.currency || "USD"}, ${duration}m. Contract ID: ${data.order_id?.order_id}.`
        );
        fetchAccount(brokerId);
        fetchPositions(brokerId);
      } else {
        pushLog(`Order failed: ${data.detail || data.error || "Unknown error"}`);
      }
    } catch (err: any) {
      pushLog(`Order failed: ${err.message || err}`);
    } finally {
      setPlacingOrder(false);
    }
  };

  const handleClosePosition = async (pos: OpenPosition) => {
    if (!brokerId) return;
    try {
      const res = await fetch("/api/brokers/close-position", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(await userHeader()) },
        body: JSON.stringify({ broker_id: brokerId, symbol: pos.symbol }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        pushLog(`Position ${pos.order_id} closed.`);
        fetchAccount(brokerId);
        fetchPositions(brokerId);
      } else {
        pushLog(`Close failed for ${pos.order_id}: ${data.detail || data.error || "Contract may not be eligible for early exit."}`);
      }
    } catch (err: any) {
      pushLog(`Close failed: ${err.message || err}`);
    }
  };

  // ── Autonomous desk pipelines (ported from the original SANS desk) ───
  // Reference spot price used ONLY as the AI analysis input -- the same
  // static table the original desk shipped with. Stake sizing for real
  // orders never depends on it.
  const getAssetRefPrice = (s: string): number => {
    if (s.includes("EURUSD")) return 1.0825;
    if (s.includes("GBPUSD")) return 1.2643;
    if (s.includes("USDJPY")) return 156.425;
    if (s.includes("XAU") || s.includes("GOLD")) return 2420.5;
    if (s.includes("BTC")) return 91245;
    return 1.152;
  };

  const deskProfile = () => {
    let riskAppetite = "Aggressive";
    let tradingGoal = "Capital Expansion & Systematic Arbitrage";
    let userIdentity = "Priv Desk Operator";
    for (const key of ["priv_profile", "xm_user_profile"]) {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) continue;
        const p = JSON.parse(raw);
        if (p?.riskAppetite) riskAppetite = p.riskAppetite;
        if (p?.tradingGoal) tradingGoal = p.tradingGoal;
        if (p?.firstName) userIdentity = `${p.firstName} ${p.lastName || ""}`.trim();
        break;
      } catch (_) {
        /* try the next legacy key */
      }
    }
    return { riskAppetite, tradingGoal, userIdentity, leverage: 20 };
  };

  const runAutonomousAnalysis = async () => {
    if (!brokerId) {
      pushAutoLog("Link a Deriv account before running analysis.");
      return;
    }
    setIsAnalyzing(true);
    setAutoAnalysis(null);
    try {
      const profile = deskProfile();
      const res = await fetch("/api/autonomous/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: selectedSymbol,
          price: getAssetRefPrice(selectedSymbol),
          balance: account?.balance || 0,
          news: [],
          technicalIndicators: { screener: "Terminal desk", sentiment: "Live session" },
          ...profile,
        }),
      });
      if (!res.ok) throw new Error("Sovereign analyst node offline.");
      const result: AutonomousAnalysis = await res.json();
      setAutoAnalysis(result);
      pushAutoLog(
        `Analysis complete: ${result.action} ${result.lotSize} lots at ${result.confidence}% confidence.`
      );
    } catch (err: any) {
      pushAutoLog(`Analysis failed: ${err.message || err}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const containerRef = useRef<HTMLDivElement>(null);
  const activeTv = tvSymbolFor(selectedSymbol);

  useEffect(() => {
    if (!activeTv) return; // synthetic index: NativeChart handles rendering instead
    if (containerRef.current) {
      containerRef.current.innerHTML = "";
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
      script.type = "text/javascript";
      script.async = true;
      script.innerHTML = JSON.stringify({
        autosize: true,
        symbol: activeTv,
        interval: "15",
        timezone: "Etc/UTC",
        theme: "dark",
        style: "1",
        locale: "en",
        enable_publishing: false,
        allow_symbol_change: false,
        studies: ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
        support_gestures: true,
        container_id: "tradingview_chart_frame",
      });
      containerRef.current.appendChild(script);
    }
  }, [activeTv]);

  const [calcStake, setCalcStake] = useState(10);
  const [calcPayoutPct, setCalcPayoutPct] = useState(82);
  const calcPayout = (calcStake * calcPayoutPct) / 100;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <span className="font-mono text-[10px] text-zinc-500 tracking-wider">
          BROKER TERMINAL
          {showMiniApp && <span className="text-zinc-300"> · RISE &amp; FALL MINI APP</span>}
        </span>
        <div className="flex items-center gap-3">
          {showMiniApp && (
            <span className="font-mono text-[9px] text-zinc-600 hidden md:inline">
              Uses your connected Deriv session from Priv — no separate sign-in needed.
            </span>
          )}
          <button
            type="button"
            disabled={miniAppLoading}
            onClick={() => {
              if (showMiniApp) {
                setShowMiniApp(false);
              } else {
                void openMiniApp();
              }
            }}
            className={`flex items-center gap-2 px-3.5 py-2 rounded font-mono text-xs border transition disabled:opacity-60 ${
              showMiniApp
                ? "bg-white/10 hover:bg-white/15 text-white border-white/15"
                : "bg-white text-black border-white hover:bg-neutral-200"
            }`}
          >
            {miniAppLoading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> CONNECTING...
              </>
            ) : showMiniApp ? (
              <>
                <X className="w-3.5 h-3.5" /> CLOSE MINI APP
              </>
            ) : (
              <>
                <Maximize2 className="w-3.5 h-3.5" /> RISE &amp; FALL MINI APP
              </>
            )}
          </button>
        </div>
      </div>

      {showMiniApp ? (
        <div className="metric-card rounded border border-white/10 bg-neutral-950/5 overflow-hidden h-[calc(100vh-240px)] min-h-[640px]">
          <iframe
            src={miniAppSrc}
            title="Priv Core mini — Rise & Fall"
            className="w-full h-full bg-white"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; payment"
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <div className="xl:col-span-4 flex flex-col gap-6">
        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
            <span className="font-mono text-[10px] text-zinc-500 tracking-wider">
              DERIV ACCOUNT{" "}
              <span className="text-zinc-300">
                {activeLogin
                  ? `${activeLogin} (${activeMode.toUpperCase()})`
                  : activeMode === "demo" ? "DEMO — NO ACCOUNT" : "LIVE — NO ACCOUNT"}
              </span>
            </span>
            <span
              className={`flex items-center gap-1.5 font-mono text-[9px] uppercase px-2 py-0.5 rounded border ${
                isConnected === null
                  ? "bg-zinc-500/5 text-zinc-400 border-zinc-500/30"
                  : isConnected
                  ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/30"
                  : "bg-red-500/5 text-red-500 border-red-500/30"
              }`}
            >
              {isConnected === null ? (
                <RefreshCw className="w-3 h-3 animate-spin" />
              ) : isConnected ? (
                <Wifi className="w-3 h-3" />
              ) : (
                <WifiOff className="w-3 h-3" />
              )}
              {isConnected === null ? "Checking..." : isConnected ? "Live" : "Offline"}
            </span>
          </div>

          {!brokerId ? (
            <div className="p-6 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
              No Deriv {activeMode} account linked. Connect one under Profile → Broker Connections,
              then return here to trade it.
            </div>
          ) : !isConnected && isConnected !== null ? (
            <div className="p-6 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
              Deriv broker connection is offline. This is managed server-side by Priv - no user login required.
            </div>
          ) : (
            <div className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="p-3 border border-white/5 bg-neutral-950/40 rounded">
                  <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Balance</span>
                  <span className="text-lg font-mono text-white font-bold">
                    {account && typeof account.balance === "number" ? `${account.currency} ${account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
                  </span>
                </div>
                <div className="p-3 border border-white/5 bg-neutral-950/40 rounded">
                  <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Account Type</span>
                  <span className="text-lg font-mono text-zinc-300 font-bold uppercase">{account?.account_type || "—"}</span>
                </div>
              </div>
              <div className="text-[10px] font-mono text-zinc-600">{account?.account_id || ""}</div>
            </div>
          )}
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
            <span className="font-serif italic text-white flex items-center font-normal">
              <Activity className="w-4 h-4 mr-2 text-stone-400" />
              Order Dispatch
            </span>
          </div>

          {!isConnected ? (
            <div className="p-6 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
              Order dispatch unavailable while Deriv connection is offline.
            </div>
          ) : (
            <form onSubmit={handlePlaceOrder} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Symbol</label>
                <SymbolPicker
                  symbols={derivSymbols}
                  value={selectedSymbol}
                  onChange={setSelectedSymbol}
                  loading={symbolsLoading}
                  error={symbolsError}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setOrderSide("BUY")}
                  className={`py-3 rounded text-xs font-mono font-bold flex items-center justify-center gap-1 border ${
                    orderSide === "BUY" ? "bg-emerald-500 text-black border-emerald-500" : "bg-neutral-950 text-emerald-500 border-white/5"
                  }`}
                >
                  <TrendingUp className="w-4 h-4" /> CALL
                </button>
                <button
                  type="button"
                  onClick={() => setOrderSide("SELL")}
                  className={`py-3 rounded text-xs font-mono font-bold flex items-center justify-center gap-1 border ${
                    orderSide === "SELL" ? "bg-red-500 text-black border-red-500" : "bg-neutral-950 text-red-500 border-white/5"
                  }`}
                >
                  <TrendingDown className="w-4 h-4" /> PUT
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div className="space-y-1">
                  <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">
                    Stake ({account?.currency || "USD"})
                  </label>
                  <input
                    type="number"
                    min={1}
                    step={1}
                    value={stake}
                    onChange={(e) => setStake(parseFloat(e.target.value) || 0)}
                    className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                  />
                </div>
                <div className="space-y-1">
                  <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Duration (min)</label>
                  <input
                    type="number"
                    min={1}
                    max={60}
                    step={1}
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value) || 1)}
                    className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">
                  Quick sizing — risk % of balance
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={0.1}
                    max={100}
                    step={0.1}
                    value={riskPct}
                    onChange={(e) => setRiskPct(parseFloat(e.target.value) || 0)}
                    className="flex-1 bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                  />
                  <button
                    type="button"
                    disabled={!account}
                    onClick={() => {
                      if (!account || typeof account.balance !== "number") return;
                      const s = Math.round(account.balance * riskPct) / 100;
                      setStake(Math.max(0.35, s));
                      pushLog(`Risk sizing applied: ${riskPct}% of balance = stake ${Math.max(0.35, s).toFixed(2)} ${account.currency || "USD"}.`);
                    }}
                    className="px-3 py-2.5 rounded border border-white/10 bg-white/5 hover:bg-white/10 text-white font-mono text-xs disabled:opacity-50"
                  >
                    APPLY
                  </button>
                </div>
                {account && typeof account.balance === "number" && (
                  <span className="block text-[9px] font-mono text-zinc-600">
                    {riskPct}% of {account.currency} {account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                )}
              </div>

              <button
                type="submit"
                disabled={placingOrder}
                className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-3 rounded flex items-center justify-center gap-2"
              >
                {placingOrder ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> SUBMITTING...
                  </>
                ) : (
                  "PLACE ORDER"
                )}
              </button>
            </form>
          )}
        </div>
      </div>

      <div className="xl:col-span-5 flex flex-col gap-6">
        <div className="metric-card rounded border border-white/10 bg-neutral-950/5 h-[420px] overflow-hidden">
          {activeTv ? (
            <div ref={containerRef} id="tradingview_chart_frame" className="w-full h-full" />
          ) : (
            <NativeChart symbol={selectedSymbol} getHeaders={userHeader} />
          )}
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <span className="font-mono text-[10px] text-zinc-500 tracking-wider">OPEN POSITIONS ({positions.length})</span>
          </div>
          {positions.length === 0 ? (
            <div className="py-8 text-center font-mono text-[11px] text-zinc-600">No open positions.</div>
          ) : (
            <div className="space-y-2">
              {positions.map((pos) => (
                <div
                  key={pos.order_id}
                  className="flex items-center justify-between p-3 border border-white/5 bg-neutral-950/40 rounded text-xs font-mono"
                >
                  <div>
                    <div className="text-white font-bold">
                      {pos.symbol || "—"} · {pos.contract_type}
                    </div>
                    <div className="text-zinc-500 text-[10px]">
                      Stake {pos.buy_price} · Payout {pos.payout} · #{pos.order_id}
                    </div>
                  </div>
                  <button
                    onClick={() => handleClosePosition(pos)}
                    className="p-2 bg-white/5 rounded hover:bg-red-500/10 hover:text-red-400"
                    title="Close position"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="xl:col-span-3 flex flex-col gap-6">
        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <span className="font-mono text-[10px] text-zinc-500 tracking-wider flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5" /> SANS AUTONOMOUS DESK
            </span>
            <span
              className={`font-mono text-[9px] px-2 py-0.5 rounded border ${
                canAutoExecute
                  ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/30"
                  : canUseDesk
                  ? "bg-amber-500/5 text-amber-400 border-amber-500/30"
                  : "bg-zinc-500/5 text-zinc-400 border-zinc-500/30"
              }`}
            >
              {canAutoExecute ? "AUTONOMOUS" : canUseDesk ? "SOVEREIGN" : "LOCKED"}
            </span>
          </div>

          {!canUseDesk ? (
            <div className="space-y-3">
              <div className="p-4 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500 flex flex-col items-center gap-2">
                <Lock className="w-4 h-4 text-zinc-500" />
                AI analysis and autonomous execution are reserved for the Sovereign and Autonomous tiers.
              </div>
              <Link
                to="/dashboard/billing"
                className="block w-full text-center bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-2.5 rounded font-mono"
              >
                VIEW PLANS
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => void runAutonomousAnalysis()}
                disabled={isAnalyzing}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded text-xs font-mono font-bold border border-white/10 bg-white/5 hover:bg-white/10 text-white disabled:opacity-60"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> ANALYZING...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" /> AI ANALYZE
                  </>
                )}
              </button>

              {autoAnalysis && (
                <div className="p-3 border border-white/5 bg-neutral-950/40 rounded space-y-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={`font-mono text-xs font-bold ${
                        autoAnalysis.action === "BUY"
                          ? "text-emerald-400"
                          : autoAnalysis.action === "SELL"
                          ? "text-red-400"
                          : "text-zinc-300"
                      }`}
                    >
                      {autoAnalysis.action}
                    </span>
                    <span className="font-mono text-[10px] text-zinc-500">
                      CONFIDENCE {autoAnalysis.confidence}%
                    </span>
                  </div>
                  <div className="h-1 rounded bg-white/5 overflow-hidden">
                    <div
                      className={`h-full ${autoAnalysis.action === "SELL" ? "bg-red-500" : "bg-emerald-500"}`}
                      style={{ width: `${Math.min(100, Math.max(0, autoAnalysis.confidence || 0))}%` }}
                    />
                  </div>
                  <div className="grid grid-cols-3 gap-2 font-mono text-[10px]">
                    <div>
                      <span className="text-zinc-500 block">LOTS</span>
                      <span className="text-white">{autoAnalysis.lotSize}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block">SL</span>
                      <span className="text-white">{autoAnalysis.stopLoss}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block">TP</span>
                      <span className="text-white">{autoAnalysis.takeProfit}</span>
                    </div>
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-relaxed whitespace-pre-wrap">
                    {autoAnalysis.reasoning}
                  </p>
                </div>
              )}

              <label className="flex items-center gap-2 text-[9px] font-mono text-zinc-400 uppercase tracking-wider select-none">
                <input
                  type="checkbox"
                  checked={scanAllMarkets}
                  disabled={autotrader.status.armed}
                  onChange={(e) => setScanAllMarkets(e.target.checked)}
                  className="accent-emerald-500"
                />
                Scan all markets (rotate the full Deriv universe instead of only {selectedSymbol})
              </label>

              <button
                type="button"
                disabled={!canAutoExecute || !brokerId || !isConnected || autotrader.busy}
                onClick={() => {
                  if (autotrader.status.armed) {
                    void autotrader.disarm();
                    pushAutoLog("Autonomous agent DISARMED.");
                    return;
                  }
                  const profile = deskProfile();
                  void autotrader.arm({
                    broker_id: brokerId,
                    symbol: selectedSymbol,
                    scan_all_markets: scanAllMarkets,
                    risk_appetite: profile.riskAppetite,
                    trading_goal: profile.tradingGoal,
                    user_identity: profile.userIdentity,
                    leverage: profile.leverage,
                    risk_pct: riskPct,
                    duration,
                    duration_unit: "m",
                  });
                  pushAutoLog(
                    scanAllMarkets
                      ? "Autonomous agent ARMED -- scanning all Deriv markets server-side. Stays live across tab close/logout; only Disable Agent stops it."
                      : `Autonomous agent ARMED on ${selectedSymbol} -- runs server-side, stays live across tab close/logout; only Disable Agent stops it.`
                  );
                }}
                className={`w-full py-2.5 rounded text-xs font-mono font-bold border disabled:opacity-50 disabled:cursor-not-allowed ${
                  autotrader.status.armed
                    ? "bg-red-500/10 text-red-400 border-red-500/40 hover:bg-red-500/20"
                    : "bg-emerald-500 text-black border-emerald-500 hover:bg-emerald-400"
                }`}
              >
                {autotrader.busy ? "..." : autotrader.status.armed ? "DISABLE AGENT" : "AUTONOMOUS TRADE"}
              </button>
              {autotrader.error && (
                <p className="text-[9px] text-red-400 font-mono">{autotrader.error}</p>
              )}
              {!canAutoExecute && (
                <p className="text-[9px] text-zinc-600 font-mono">
                  Auto-execution requires the Autonomous tier (admins pass). Analysis remains available.
                </p>
              )}
              {canAutoExecute && (!brokerId || !isConnected) && (
                <p className="text-[9px] text-zinc-600 font-mono">
                  Link and connect a Deriv account to arm the agent.
                </p>
              )}

              <div className="pt-2 border-t border-white/5">
                <span className="font-mono text-[9px] text-zinc-500 uppercase tracking-widest">
                  Cycle Log
                  {autotrader.status.armed && (
                    <span className="text-zinc-600 normal-case tracking-normal">
                      {" "}
                      &middot; {autotrader.status.cycles} cycles &middot; {autotrader.status.placements} placements
                      {autotrader.status.scan_all_markets && autotrader.status.universe_size
                        ? ` \u00b7 scanning ${autotrader.status.universe_size} markets`
                        : ""}
                    </span>
                  )}
                </span>
                <div className="space-y-1 max-h-[160px] overflow-y-auto font-mono text-[10px] text-zinc-400 mt-1.5">
                  {autotrader.status.logs.length === 0 ? (
                    <div className="text-zinc-600">Agent idle.</div>
                  ) : (
                    autotrader.status.logs.map((l, i) => <div key={i}>{l}</div>)
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <span className="font-mono text-[10px] text-zinc-500 tracking-wider">EXECUTION LOG</span>
          </div>
          <div className="space-y-1.5 max-h-[300px] overflow-y-auto font-mono text-[10px] text-zinc-400">
            {logs.length === 0 ? (
              <div className="text-zinc-600">No activity yet.</div>
            ) : (
              logs.map((l, i) => <div key={i}>{l}</div>)
            )}
          </div>
        </div>

        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-3">
            <span className="font-serif italic text-white flex items-center font-normal">
              <Calculator className="w-4 h-4 mr-2 text-stone-400" />
              Payout Estimator
            </span>
          </div>
          <div className="space-y-3 font-mono text-xs">
            <div className="space-y-1">
              <label className="block text-[9px] text-zinc-500 uppercase tracking-widest">Stake</label>
              <input
                type="number"
                value={calcStake}
                onChange={(e) => setCalcStake(parseFloat(e.target.value) || 0)}
                className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-white"
              />
            </div>
            <div className="space-y-1">
              <label className="block text-[9px] text-zinc-500 uppercase tracking-widest">Payout %</label>
              <input
                type="number"
                value={calcPayoutPct}
                onChange={(e) => setCalcPayoutPct(parseFloat(e.target.value) || 0)}
                className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-white"
              />
            </div>
            <div className="pt-2 border-t border-white/5 flex justify-between">
              <span className="text-zinc-500">Est. Payout</span>
              <span className="text-white font-bold">{calcPayout.toFixed(2)}</span>
            </div>
            <p className="text-[9px] text-zinc-600 leading-relaxed">
              Estimate only - actual payout is quoted live by Deriv at order time and varies with market conditions.
            </p>
          </div>
        </div>
      </div>
        </div>
      )}
    </div>
  );
}

export default function TradingTerminal() {
  return (
    <TerminalErrorBoundary>
      <TradingTerminalInner />
    </TerminalErrorBoundary>
  );
}
