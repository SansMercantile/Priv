import React, { useState, useEffect, useRef } from "react";
import {
  Activity,
  Wifi,
  WifiOff,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  X,
  Calculator,
} from "lucide-react";

// ── Real broker constant ─────────────────────────────────────────────────
// Single business-managed Deriv connection. There is no per-user broker
// login (no email/password/server) - the backend authenticates once with
// the PRIV_CORE app's API token and every user trades through that same
// connection. This intentionally replaces the old multi-broker XM/Binance/
// Coinbase tab switcher and its fake MT4/MT5-style login simulation.
const BROKER_ID = "priv_deriv";

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

const SYMBOLS = [
  { title: "EUR/USD", symbol: "frxEURUSD", tv: "FX_IDC:EURUSD" },
  { title: "GBP/USD", symbol: "frxGBPUSD", tv: "FX_IDC:GBPUSD" },
  { title: "USD/JPY", symbol: "frxUSDJPY", tv: "FX_IDC:USDJPY" },
  { title: "Volatility 100", symbol: "R_100", tv: "BINANCE:BTCUSDT" },
  { title: "Volatility 75", symbol: "R_75", tv: "BINANCE:BTCUSDT" },
];

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

  const pushLog = (msg: string) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 100));
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`/api/brokers/status/${BROKER_ID}`);
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

  const fetchAccount = async () => {
    try {
      const res = await fetch(`/api/brokers/account/${BROKER_ID}`);
      if (res.ok) {
        const data = await res.json();
        if (!data.error) setAccount(data);
      }
    } catch {}
  };

  const fetchPositions = async () => {
    try {
      const res = await fetch(`/api/brokers/positions?broker_id=${BROKER_ID}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setPositions(data);
      }
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
    fetchAccount();
    fetchPositions();
    const interval = setInterval(() => {
      fetchAccount();
      fetchPositions();
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const [selectedSymbol, setSelectedSymbol] = useState(SYMBOLS[3].symbol);
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");
  const [stake, setStake] = useState<number>(10);
  const [duration, setDuration] = useState<number>(5);
  const [placingOrder, setPlacingOrder] = useState(false);

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          broker_id: BROKER_ID,
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
        fetchAccount();
        fetchPositions();
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
    try {
      const res = await fetch("/api/brokers/close-position", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ broker_id: BROKER_ID, symbol: pos.symbol }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        pushLog(`Position ${pos.order_id} closed.`);
        fetchAccount();
        fetchPositions();
      } else {
        pushLog(`Close failed for ${pos.order_id}: ${data.detail || data.error || "Contract may not be eligible for early exit."}`);
      }
    } catch (err: any) {
      pushLog(`Close failed: ${err.message || err}`);
    }
  };

  const containerRef = useRef<HTMLDivElement>(null);
  const activeTv = SYMBOLS.find((s) => s.symbol === selectedSymbol)?.tv || "BINANCE:BTCUSDT";

  useEffect(() => {
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
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
      <div className="xl:col-span-4 flex flex-col gap-6">
        <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
            <span className="font-mono text-[10px] text-zinc-500 tracking-wider">DERIV ACCOUNT (PRIV CORE)</span>
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

          {!isConnected && isConnected !== null ? (
            <div className="p-6 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
              Deriv broker connection is offline. This is managed server-side by Priv - no user login required.
            </div>
          ) : (
            <div className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3.5">
                <div className="p-3 border border-white/5 bg-neutral-950/40 rounded">
                  <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Balance</span>
                  <span className="text-lg font-mono text-white font-bold">
                    {account ? `${account.currency} ${account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
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
                <select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className="w-full bg-neutral-950 border border-white/10 rounded p-2.5 text-xs text-white font-mono"
                >
                  {SYMBOLS.map((s) => (
                    <option key={s.symbol} value={s.symbol}>
                      {s.title} ({s.symbol})
                    </option>
                  ))}
                </select>
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
          <div ref={containerRef} id="tradingview_chart_frame" className="w-full h-full" />
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
  );
}

export default function TradingTerminal() {
  return (
    <TerminalErrorBoundary>
      <TradingTerminalInner />
    </TerminalErrorBoundary>
  );
}
