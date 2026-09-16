import React, { useEffect } from "react";
import { Link, Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth0 } from "@auth0/auth0-react";

/**
 * Public marketing landing page served at `/` for visitors who have not
 * logged in yet (mirrors public/landing.html content in React).
 * Authenticated users are sent straight to the dashboard.
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

const TICKET_ROWS: Array<[string, string, string?]> = [
  ["Entry", "8,452.10", ""],
  ["Take Profit 1", "8,461.30", "tp"],
  ["Take Profit 2", "8,470.50", "tp"],
  ["Stop Loss", "8,443.00", "sl"],
];

export default function Landing() {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();

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

          {/* Sample signal ticket */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-md p-5 shadow-2xl"
          >
            <div className="text-[10px] font-mono tracking-widest text-rose-200/70 mb-3">SAMPLE SIGNAL</div>
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-[11px] text-white/40">VOLATILITY 100 INDEX</div>
                <div className="text-xl font-bold">R_100</div>
              </div>
              <div className="text-[11px] font-semibold text-emerald-300">BUY · INSTANT EXECUTION</div>
            </div>
            <div className="space-y-2 text-[14px]">
              {TICKET_ROWS.map(([k, v, cls]) => (
                <div key={k} className="flex justify-between border-b border-white/5 pb-2">
                  <span className="text-white/45">{k}</span>
                  <span className={`font-mono font-semibold ${cls === "tp" ? "text-emerald-300" : cls === "sl" ? "text-rose-300" : "text-white"}`}>
                    {v}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs text-white/40 leading-relaxed">
              Stop loss trails to <strong className="text-white">8,452.10</strong> once Take Profit 1 is reached —
              locking in a breakeven-or-better trade automatically.
            </p>
            <p className="mt-2 text-[11px] font-mono text-white/30">basis: ATR(6.10) × 1.5 · signal strength 42/100</p>
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
    </div>
  );
}
