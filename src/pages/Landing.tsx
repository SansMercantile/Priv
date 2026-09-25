import React, { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth0 } from "@auth0/auth0-react";

/**
 * Public marketing landing page served at `/` for visitors who have not
 * logged in yet (mirrors public/landing.html content in React).
 * Authenticated users are sent straight to the dashboard.
 *
 * The signal ticket is LIVE: fetched from GET /api/signals/current (one
 * signal per 6h UTC slot, computed from real Deriv candles). A tick watcher
 * raises bottom-right toasts on TP1 (stop to breakeven), TP2 and SL.
 * A cached copy covers backend outages; the static sample only shows when
 * nothing was ever fetched.
 */
const STEPS = [
  {
    num: "01",
    title: "Choose a category",
    body: "Indices, Synthetics, Commodities, or Shares. Free accounts track one category at a time.",
  },
  {
    num: "02",
    title: "Pick your instruments",
    body: "Select the specific instruments you want Priv watching — three on the free tier, more on paid plans.",
  },
  {
    num: "03",
    title: "Receive your signal",
    body: "Entry, two take-profits, stop loss, and trailing updates — sent by email, SMS, or WhatsApp the moment a setup completes.",
  },
  {
    num: "04",
    title: "Trade it, or automate it",
    body: "Execute manually yourself, or connect your Deriv account and let Priv place, manage, and trail the trade for you.",
  },
];

interface LiveSignal {
  id: string;
  symbol: string;
  display_name: string;
  direction: "BUY" | "SELL";
  entry: number;
  take_profit_1: number;
  take_profit_2: number;
  stop_loss: number;
  atr: number;
  timeframe: string;
  slot_start_utc: string;
  app_id?: string;
}

const STATIC_SIGNAL: LiveSignal = {
  id: "static-sample",
  symbol: "R_100",
  display_name: "VOLATILITY 100 INDEX",
  direction: "BUY",
  entry: 8452.1,
  take_profit_1: 8461.3,
  take_profit_2: 8470.5,
  stop_loss: 8443.0,
  atr: 6.1,
  timeframe: "1H",
  slot_start_utc: "",
};

interface Toast {
  id: string;
  title: string;
  body: string;
  kind: "tp1" | "tp2" | "sl" | "info";
}

function useLiveSignal() {
  const [signal, setSignal] = useState<LiveSignal | null>(null);
  const [live, setLive] = useState(false);
  const [sentLocal, setSentLocal] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/signals/current");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const body = await res.json();
        const data = (body?.data || body) as LiveSignal;
        if (!data || !data.entry) throw new Error("bad payload");
        if (cancelled) return;
        setSignal(data);
        setLive(true);
        try {
          localStorage.setItem("priv_live_signal", JSON.stringify(data));
        } catch (_) {}
      } catch (_) {
        if (cancelled) return;
        try {
          const cached = localStorage.getItem("priv_live_signal");
          if (cached) {
            const data = JSON.parse(cached) as LiveSignal;
            if (data && data.entry) {
              setSignal(data);
              setLive(false);
              return;
            }
          }
        } catch (_) {}
        setSignal(STATIC_SIGNAL);
        setLive(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!signal?.slot_start_utc) {
      setSentLocal("");
      return;
    }
    try {
      setSentLocal(new Date(signal.slot_start_utc).toLocaleString());
    } catch (_) {
      setSentLocal(signal.slot_start_utc);
    }
  }, [signal]);

  return { signal: signal || STATIC_SIGNAL, live, sentLocal };
}

function useSignalToasts(signal: LiveSignal | null, live: boolean) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const firedRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!signal || !live || !signal.app_id || signal.id === "static-sample") return;
    const key = `priv_toast_fired_${signal.id}`;
    try {
      (JSON.parse(localStorage.getItem(key) || "[]") as string[]).forEach((k) => firedRef.current.add(k));
    } catch (_) {}
    const persist = () => {
      try {
        localStorage.setItem(key, JSON.stringify(Array.from(firedRef.current)));
      } catch (_) {}
    };
    const push = (kind: Toast["kind"], title: string, body: string) => {
      const id = `${signal.id}-${kind}`;
      if (firedRef.current.has(id)) return;
      firedRef.current.add(id);
      persist();
      setToasts((prev) => [...prev.slice(-2), { id, kind, title, body }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 12000);
    };

    let ws: WebSocket | null = null;
    let closed = false;
    try {
      ws = new WebSocket(`wss://ws.derivws.com/websockets/v3?app_id=${signal.app_id}`);
    } catch (_) {
      return;
    }
    const isBuy = signal.direction === "BUY";
    ws.onopen = () => {
      if (!closed) ws?.send(JSON.stringify({ ticks: signal.symbol, subscribe: 1 }));
    };
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        const quote = Number(msg?.tick?.quote);
        if (!Number.isFinite(quote)) return;
        if (isBuy) {
          if (quote >= signal.take_profit_1) {
            push("tp1", "TP1 hit — stop moved to breakeven",
              `${signal.symbol} reached ${signal.take_profit_1}. Stop loss trailed to entry ${signal.entry}.`);
          }
          if (quote >= signal.take_profit_2) {
            push("tp2", "TP2 hit — full target reached", `${signal.symbol} reached ${signal.take_profit_2}.`);
          }
          if (quote <= signal.stop_loss) {
            push("sl", "Stop loss hit", `${signal.symbol} fell to ${signal.stop_loss}. Position closed.`);
          }
        } else {
          if (quote <= signal.take_profit_1) {
            push("tp1", "TP1 hit — stop moved to breakeven",
              `${signal.symbol} dropped to ${signal.take_profit_1}. Stop loss trailed to entry ${signal.entry}.`);
          }
          if (quote <= signal.take_profit_2) {
            push("tp2", "TP2 hit — full target reached", `${signal.symbol} dropped to ${signal.take_profit_2}.`);
          }
          if (quote >= signal.stop_loss) {
            push("sl", "Stop loss hit", `${signal.symbol} rose to ${signal.stop_loss}. Position closed.`);
          }
        }
      } catch (_) {}
    };
    ws.onerror = () => {};
    return () => {
      closed = true;
      try {
        ws?.close();
      } catch (_) {}
    };
  }, [signal, live]);

  const dismiss = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));
  return { toasts, dismiss };
}

const TOAST_STYLES: Record<Toast["kind"], string> = {
  tp1: "border-amber-400/40",
  tp2: "border-emerald-400/40",
  sl: "border-rose-500/40",
  info: "border-white/15",
};

interface HistSignal {
  id: string;
  symbol: string;
  display_name?: string;
  direction: string;
  entry: number;
  take_profit_1: number;
  take_profit_2: number;
  stop_loss: number;
  slot_start_utc?: string;
  created_at?: string;
  timeframe?: string;
}

function useSignalHistory() {
  const [history, setHistory] = useState<HistSignal[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/signals/history?limit=6");
        if (!res.ok) return;
        const body = await res.json();
        const glob = body?.data?.global ?? [];
        if (!cancelled && Array.isArray(glob)) setHistory(glob.slice(0, 5));
      } catch (_) {
        /* history is enhancement-only; ticket still renders */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return history;
}

type SignalStatus = "Hold" | "TP1 Hit" | "TP2 Hit" | "SL Hit" | "Expired" | "…";

const STATUS_STYLES: Record<string, string> = {
  "Hold": "text-sky-300 border-sky-400/30 bg-sky-400/10",
  "TP1 Hit": "text-amber-300 border-amber-400/30 bg-amber-400/10",
  "TP2 Hit": "text-emerald-300 border-emerald-400/30 bg-emerald-400/10",
  "SL Hit": "text-rose-300 border-rose-500/30 bg-rose-500/10",
  "Expired": "text-zinc-400 border-white/10 bg-white/5",
  "…": "text-zinc-500 border-white/10 bg-white/5",
};

// First-touch outcome over 1h candles after the signal: TP2 > TP1 > SL by
// touch order. Untouched + fresh slot => Hold; untouched + older => Expired.
function computeOutcome(
  direction: string, tp1: number, tp2: number, sl: number,
  candles: Array<{ high: number; low: number }>, slotAgeH: number
): SignalStatus {
  const isBuy = direction === "BUY";
  for (const c of candles) {
    const hitTp2 = isBuy ? c.high >= tp2 : c.low <= tp2;
    const hitTp1 = isBuy ? c.high >= tp1 : c.low <= tp1;
    const hitSl = isBuy ? c.low <= sl : c.high >= sl;
    if (hitTp2) return "TP2 Hit";
    if (hitTp1) return "TP1 Hit";
    if (hitSl) return "SL Hit";
  }
  return slotAgeH <= 30 ? "Hold" : "Expired";
}

function alternativeOrder(
  direction: string, entry: number, last: number | null
): string | null {
  if (last === null || !Number.isFinite(entry)) return null;
  const px = (n: number) =>
    n.toLocaleString(undefined, { maximumFractionDigits: 5 });
  if (direction === "BUY") {
    return last < entry ? `Buy Stop @ ${px(entry)}` : `Buy Limit @ ${px(entry)}`;
  }
  return last > entry ? `Sell Stop @ ${px(entry)}` : `Sell Limit @ ${px(entry)}`;
}

function useSignalStatus(item: HistSignal | null, active: boolean, appId: string) {
  const [status, setStatus] = useState<SignalStatus>("…");
  const [alt, setAlt] = useState<string | null>(null);
  const [sentLocal, setSentLocal] = useState("");

  useEffect(() => {
    if (!item || !active) return;
    let cancelled = false;
    try {
      const d = new Date(item.slot_start_utc || item.created_at || "");
      if (!isNaN(d.getTime())) setSentLocal(d.toLocaleString());
    } catch (_) {}
    let ws: WebSocket | null = null;
    let closed = false;
    try {
      ws = new WebSocket(`wss://ws.derivws.com/websockets/v3?app_id=${appId || "1089"}`);
    } catch (_) {
      setStatus("Hold");
      return;
    }
    ws.onopen = () => {
      if (closed) return;
      ws?.send(JSON.stringify({
        ticks_history: item.symbol, style: "candles",
        granularity: 3600, count: 30, end: "latest",
      }));
    };
    ws.onmessage = (ev) => {
      if (cancelled || closed) return;
      try {
        const msg = JSON.parse(ev.data);
        if (msg.error || !Array.isArray(msg.candles)) return;
        const candles = msg.candles
          .map((c: any) => ({ high: Number(c.high), low: Number(c.low), close: Number(c.close) }))
          .filter((c: any) => Number.isFinite(c.high) && Number.isFinite(c.low));
        if (!candles.length) return;
        const slotStart = new Date(item.slot_start_utc || item.created_at || Date.now()).getTime();
        const ageH = Math.max(0, (Date.now() - slotStart) / 3600000);
        const outcome = computeOutcome(
          item.direction, item.take_profit_1, item.take_profit_2,
          item.stop_loss, candles, ageH);
        const last = candles.length ? candles[candles.length - 1].close : null;
        if (!cancelled) {
          setStatus(outcome);
          setAlt(outcome === "Hold" ? alternativeOrder(item.direction, item.entry, last) : null);
        }
      } catch (_) {}
      try {
        ws?.close();
      } catch (_) {}
    };
    ws.onerror = () => {
      if (!cancelled) setStatus("Hold");
    };
    const fallback = window.setTimeout(() => {
      if (!cancelled) setStatus((s) => (s === "…" ? "Hold" : s));
    }, 8000);
    return () => {
      cancelled = true;
      closed = true;
      window.clearTimeout(fallback);
      try {
        ws?.close();
      } catch (_) {}
    };
  }, [item?.id, active]);

  return { status, alt, sentLocal };
}

function HistorySlide({ item, active, appId }: { item: HistSignal; active: boolean; appId: string }) {
  const { status, alt, sentLocal } = useSignalStatus(item, active, appId);
  const isBuy = item.direction === "BUY";
  const rows: Array<[string, number]> = [
    ["Entry", item.entry],
    ["Take Profit 1", item.take_profit_1],
    ["Take Profit 2", item.take_profit_2],
    ["Stop Loss", item.stop_loss],
  ];
  return (
    <div>
      <div className="flex items-start justify-between mb-1">
        <div>
          <div className="text-[11px] text-white/40">{item.display_name || item.symbol}</div>
          <div className="text-xl font-bold">{item.symbol}</div>
        </div>
        <span className={`text-[10px] font-mono font-bold uppercase px-2 py-1 rounded border ${STATUS_STYLES[status]}`}>
          {status === "…" ? "tracking…" : status}
        </span>
      </div>
      <div className={`text-[11px] font-semibold mb-3 ${isBuy ? "text-emerald-300" : "text-rose-300"}`}>
        {item.direction} · {item.timeframe || "1H"}
      </div>
      <div className="space-y-2 text-[14px]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between border-b border-white/5 pb-2">
            <span className="text-white/45">{k}</span>
            <span className="font-mono font-semibold text-white">
              {Number(v).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
      {alt && (
        <p className="mt-3 text-xs font-mono text-sky-300/90">
          Alternative: {item.symbol} {alt} · TP1 {Number(item.take_profit_1).toLocaleString()} &amp; TP2 {Number(item.take_profit_2).toLocaleString()} · SL {Number(item.stop_loss).toLocaleString()}
        </p>
      )}
      <p className="mt-2 text-[11px] font-mono text-white/30">
        {sentLocal ? `sent ${sentLocal}` : ""}
      </p>
    </div>
  );
}

function SignalCarousel({ signal, live, sentLocal, isBuy, rows, history, appId }: {
  signal: LiveSignal; live: boolean; sentLocal: string; isBuy: boolean;
  rows: Array<[string, number, string?]>; history: HistSignal[]; appId: string;
}) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const total = 1 + history.length;

  useEffect(() => {
    if (paused || total <= 1) return;
    const t = window.setInterval(() => setIndex((i) => (i + 1) % total), 5000);
    return () => window.clearInterval(t);
  }, [paused, total]);

  return (
    <div
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {index === 0 ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] font-mono tracking-widest text-rose-200/70">
              {live ? "LIVE SIGNAL" : "SAMPLE SIGNAL"}
            </div>
            {live && <div className="flex items-center gap-1.5 text-[10px] text-emerald-300"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />LIVE</div>}
          </div>
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="text-[11px] text-white/40">{signal.display_name}</div>
              <div className="text-xl font-bold">{signal.symbol}</div>
            </div>
            <div className={`text-[11px] font-semibold ${isBuy ? "text-emerald-300" : "text-rose-300"}`}>
              {signal.direction} · {signal.timeframe}
            </div>
          </div>
          <div className="space-y-2 text-[14px]">
            {rows.map(([k, v, cls]) => (
              <div key={k} className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-white/45">{k}</span>
                <span className={`font-mono font-semibold ${cls === "tp" ? "text-emerald-300" : cls === "sl" ? "text-rose-300" : "text-white"}`}>
                  {v.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-white/40 leading-relaxed">
            Stop loss trails to <strong className="text-white">{signal.entry.toLocaleString()}</strong> once Take
            Profit 1 is reached — locking in a breakeven-or-better trade automatically.
          </p>
          <p className="mt-2 text-[11px] font-mono text-white/30">
            basis: ATR({signal.atr}) · {signal.timeframe}
            {sentLocal ? ` · sent ${sentLocal}` : ""}
          </p>
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] font-mono tracking-widest text-rose-200/70">
              SIGNAL HISTORY · {index} OF {history.length}
            </div>
          </div>
          <HistorySlide item={history[index - 1]} active={true} appId={appId} />
        </div>
      )}
      {total > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <button
            onClick={() => setIndex((index - 1 + total) % total)}
            className="px-3 py-1 rounded-lg border border-white/15 text-white/60 hover:text-white text-sm"
            aria-label="Previous signal"
          >
            ‹
          </button>
          <div className="flex gap-1.5">
            {Array.from({ length: total }).map((_, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                aria-label={`Signal ${i + 1}`}
                className={`h-1.5 rounded-full transition-all ${i === index ? "w-6 bg-rose-400" : "w-1.5 bg-white/20 hover:bg-white/40"}`}
              />
            ))}
          </div>
          <button
            onClick={() => setIndex((index + 1) % total)}
            className="px-3 py-1 rounded-lg border border-white/15 text-white/60 hover:text-white text-sm"
            aria-label="Next signal"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}

export default function Landing() {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();
  const { signal, live, sentLocal } = useLiveSignal();
  const history = useSignalHistory();
  const { toasts, dismiss } = useSignalToasts(live ? signal : null, live);

  useEffect(() => {
    document.title = "Priv — Intelligent Trading. Limitless Potential.™";
  }, []);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const startFree = () =>
    loginWithRedirect({
      authorizationParams: { screen_hint: "signup" },
      appState: { returnTo: "/dashboard" },
    });
  const signIn = () => loginWithRedirect({ appState: { returnTo: "/dashboard" } });

  const isBuy = signal.direction === "BUY";
  const rows: Array<[string, number, string?]> = [
    ["Entry", signal.entry, ""],
    ["Take Profit 1", signal.take_profit_1, "tp"],
    ["Take Profit 2", signal.take_profit_2, "tp"],
    ["Stop Loss", signal.stop_loss, "sl"],
  ];

  return (
    <div className="min-h-screen bg-black text-white neural-grid matrix-bg">
      {/* Nav */}
      <header className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 py-5">
        <div className="flex items-center gap-2.5">
          <svg viewBox="0 0 100 100" fill="none" className="w-6 h-6">
            <defs>
              <linearGradient id="priv-g" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff4b72" />
                <stop offset="50%" stopColor="#e11d48" />
                <stop offset="100%" stopColor="#9f1239" />
              </linearGradient>
            </defs>
            <path d="M50 15 L85 50 L50 85 L15 50 Z" stroke="url(#priv-g)" strokeWidth="6" strokeLinejoin="round" />
            <path d="M50 28 L72 50 L50 72 L28 50 Z" fill="url(#priv-g)" opacity="0.35" />
            <circle cx="50" cy="50" r="8" fill="#ffffff" />
          </svg>
          <span className="font-bold tracking-tight text-[15.5px]">Priv</span>
        </div>
        <div className="flex items-center gap-3 text-[13.5px]">
          <a href="#how-it-works" className="hidden sm:inline text-white/60 hover:text-white">How it works</a>
          <a href="#pricing" className="hidden sm:inline text-white/60 hover:text-white">Pricing</a>
          <button
            onClick={signIn}
            className="px-4 py-2 rounded-lg border border-white/15 text-white/80 hover:text-white hover:border-white/30"
          >
            Sign in
          </button>
        </div>
      </header>

      {/* Hero */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid md:grid-cols-2 gap-10 items-center pt-10 pb-16">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <div className="inline-flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-rose-200/80 border border-rose-500/30 rounded-full px-3 py-1.5 mb-5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#ff4b72] animate-pulse" />
              Signals delivered the moment a setup forms
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.08]">
              Precision entries, read from the market — not guessed at.
            </h1>
            <p className="mt-4 text-white/55 text-[15px] leading-relaxed max-w-xl">
              Priv analyzes price action across Indices, Synthetics, Commodities, and Shares, then sends you the
              exact entry, two take-profit levels, and a stop loss that trails into profit as the trade moves. Act on
              it yourself, or let Priv execute it directly on your connected Deriv account.
            </p>
            <p className="mt-3 text-[13px] text-white/40">A Sans Mercantile fintech product</p>
            <div className="flex flex-wrap gap-3 mt-6">
              <button
                onClick={startFree}
                className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#ff4b72] to-[#e11d48] font-semibold text-[15px] shadow-[0_8px_30px_rgba(225,29,72,0.35)] hover:brightness-110"
              >
                Start free — 3 signals
              </button>
              <a
                href="#how-it-works"
                className="px-6 py-3 rounded-xl border border-white/15 text-white/80 hover:text-white hover:border-white/30 text-[15px]"
              >
                See how it works
              </a>
            </div>
            <p className="mt-3 text-xs text-white/35">No card required for the free tier. Cancel anytime.</p>
          </motion.div>

          {/* Live signal ticket */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-md p-5 shadow-2xl"
          >
            <SignalCarousel
              signal={signal}
              live={live}
              sentLocal={sentLocal}
              isBuy={isBuy}
              rows={rows}
              history={history}
              appId={signal.app_id || ""}
            />
          </motion.div>
        </div>

        {/* How it works */}
        <section id="how-it-works" className="py-14 border-t border-white/5">
          <p className="text-[11px] font-mono tracking-widest text-rose-200/70 mb-2">HOW PRIV WORKS</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-8">Four steps, from setup to signal in your pocket.</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {STEPS.map((s) => (
              <div key={s.num} className="rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="text-2xl font-bold text-rose-400/80 font-mono">{s.num}</div>
                <h3 className="mt-2 font-semibold">{s.title}</h3>
                <p className="mt-1.5 text-[13px] text-white/50 leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Trust */}
        <section id="trust" className="py-14 border-t border-white/5">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Your account, your funds, your control.</h2>
          <p className="mt-3 text-white/55 text-[15px] max-w-2xl leading-relaxed">
            Priv connects to your own Deriv account via official OAuth — funds never leave your broker, orders are
            placed in your name, and every action is logged to an auditable trail. Kill-switch included.
          </p>
          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={startFree}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-[#ff4b72] to-[#e11d48] font-semibold text-[15px] hover:brightness-110"
            >
              Start free — 3 signals
            </button>
            <Link to="/dashboard" className="px-6 py-3 rounded-xl border border-white/15 text-white/80 hover:text-white text-[15px]">
              Open the app
            </Link>
          </div>
        </section>
      {/* Pricing — mirrors /api/v1/payment/plans exactly */}
      <section id="pricing" className="py-14 border-t border-white/5">
        <p className="text-[11px] font-mono tracking-widest text-rose-200/70 mb-2">PRICING</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">One plan for every pace.</h2>
        <p className="text-white/55 text-[15px] max-w-2xl mb-8">
          Start free. Upgrade when the signals start paying for themselves. Prices in USD, billed in Rand at checkout.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { name: "Priv Signals Free", price: "$0", per: "/mo", tag: "Try Priv's AI trading signals at no cost.", feats: ["4 free AI signals / day", "Synthetics market only", "Entry, TP1 & TP2, trailing Stop Loss", "Email or SMS delivery", "Manual execution only"], cta: "Start free" },
            { name: "Priv Signal Pro", price: "$29", per: "/mo", tag: "More signals across more instruments.", feats: ["8 signals / day: Synthetics, Indices, Commodities & Shares", "Entry, TP1 & TP2, trailing Stop Loss", "Email, SMS, or WhatsApp", "Manual execution only"], cta: "Go Pro" },
            { name: "Priv Signal Elite", price: "$79", per: "/mo", tag: "High-volume signals for active intraday traders.", feats: ["16 signals / day, all asset categories", "Real-time entry, SL, TP1, TP2, dynamic trailing stops", "Instant delivery, priority routing", "Manual execution only"], cta: "Go Elite" },
            { name: "Priv Signal Sovereign", price: "$149", per: "/mo", tag: "Complete coverage plus event setups.", feats: ["32 signals / day, all categories", "Exclusive Event-Driven Signals: NFP, CPI, rate decisions", "Prop-firm parameters (FTMO / funded compliance)", "Priority instant delivery"], cta: "Go Sovereign" },
            { name: "Priv Autonomous", price: "$199", per: "/mo", tag: "Priv trades your connected Deriv account for you.", feats: ["Unlimited active setups, all categories", "Autonomous execution via Deriv API", "Entry management, TP scaling, SL adjustment, trailing locks", "Hands-free execution"], cta: "Go Autonomous" },
          ].map((p) => (
            <div key={p.name} className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 flex flex-col">
              <h3 className="font-semibold text-white">{p.name}</h3>
              <p className="text-xs text-white/45 mt-1">{p.tag}</p>
              <p className="mt-3">
                <span className="text-3xl font-bold">{p.price}</span>
                <span className="text-sm text-white/40">{p.per}</span>
              </p>
              <ul className="mt-3 space-y-1.5 text-[13px] text-white/55 flex-1">
                {p.feats.map((f) => (
                  <li key={f} className="flex gap-2"><span className="text-emerald-400">✓</span>{f}</li>
                ))}
              </ul>
              <button
                onClick={startFree}
                className="mt-4 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/15 text-white text-sm font-semibold transition"
              >
                {p.cta}
              </button>
            </div>
          ))}
        </div>
      </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-6">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row justify-between gap-4">
          <div>
            <p className="text-[13px] text-white/40">A Sans Mercantile fintech product</p>
            <p className="text-[13px] text-white/60 font-semibold mt-1.5">Intelligent Trading. Limitless Potential.™</p>
          </div>
          <p className="text-xs text-white/30">© 2026 Sans Mercantile. All rights reserved.</p>
        </div>
      </footer>

      {/* Bottom-right TP/SL toasts */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-xs w-[calc(100%-2rem)]">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              className={`rounded-xl border ${TOAST_STYLES[t.kind]} bg-black/85 backdrop-blur-md p-4 shadow-2xl`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-[13px] font-semibold">{t.title}</p>
                <button onClick={() => dismiss(t.id)} className="text-white/40 hover:text-white text-sm leading-none">
                  ×
                </button>
              </div>
              <p className="mt-1 text-xs text-white/55 leading-relaxed">{t.body}</p>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
