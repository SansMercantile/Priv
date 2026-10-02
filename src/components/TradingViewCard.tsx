import React from "react";

// TradingView platform card (Connections → Broker Connections, next to
// the Deriv card). TradingView is Deriv's web-based chart-trading
// surface: connect once on Deriv's side (dashboard → CFDs → Connect to
// TradingView), then trade from TradingView in the browser -- no MT5
// terminal and no MetaApi bridge. The in-terminal platform selector
// defaults to TradingView too, where the chart widget and Order
// Dispatch already live.
export default function TradingViewCard() {
  return (
    <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3">
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
        <span className="text-zinc-300">
          TradingView (web) — trade Deriv markets from your browser, no MT5 terminal
        </span>
      </div>
      <p className="text-[11px] text-zinc-500 font-mono leading-relaxed">
        First time: open your Deriv dashboard → <span className="text-zinc-300">CFDs</span> →{" "}
        <span className="text-zinc-300">Connect to TradingView</span>, approve access, then
        choose <span className="text-zinc-300">Continue in browser</span>. After that the
        same TradingView chart is embedded in our terminal (Platform → TradingView, the
        default) with orders executed here server-side.
      </p>
      <div className="flex flex-wrap gap-2">
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="px-5 py-2.5 bg-white text-black font-mono font-bold text-xs rounded-lg hover:bg-white/90 transition"
        >
          Continue in browser
        </a>
        <a
          href="https://app.deriv.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="px-5 py-2.5 border border-white/20 text-white font-mono text-xs rounded-lg hover:bg-white/10 transition"
        >
          Open Deriv dashboard
        </a>
      </div>
    </div>
  );
}
