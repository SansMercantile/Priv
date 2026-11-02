import React, { useMemo, useState } from "react";
import { Search } from "lucide-react";
import type { DerivSymbol } from "./derivSymbols";

interface Props {
  symbols: DerivSymbol[];
  value: string;
  onChange: (code: string) => void;
  loading?: boolean;
  error?: string | null;
}

// Searchable, market-grouped picker over the FULL Deriv universe.
export default function SymbolPicker({ symbols, value, onChange, loading, error }: Props) {
  const [q, setQ] = useState("");
  const [market, setMarket] = useState<string>("all");

  const markets = useMemo(() => {
    const m = new Map<string, string>();
    symbols.forEach((s) => m.set(s.market, s.market_display_name || s.market));
    return Array.from(m.entries());
  }, [symbols]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return symbols.filter((s) => {
      if (market !== "all" && s.market !== market) return false;
      if (!needle) return true;
      return (
        s.symbol.toLowerCase().includes(needle) ||
        s.display_name.toLowerCase().includes(needle) ||
        (s.market_display_name || "").toLowerCase().includes(needle)
      );
    });
  }, [symbols, q, market]);

  const current = symbols.find((s) => s.symbol === value);

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={loading ? "Loading Deriv markets..." : `Search ${symbols.length} markets (e.g. volatility 100, EURUSD, boom)`}
          className="w-full bg-neutral-950 border border-white/10 rounded pl-8 pr-2.5 py-2.5 text-xs text-white font-mono"
        />
      </div>
      <div className="flex flex-wrap gap-1">
        <button
          type="button"
          onClick={() => setMarket("all")}
          className={`px-2 py-1 rounded text-[9px] font-mono uppercase border ${market === "all" ? "bg-white text-black border-white" : "text-zinc-400 border-white/10"}`}
        >
          All ({symbols.length})
        </button>
        {markets.map(([code, label]) => (
          <button
            type="button"
            key={code}
            onClick={() => setMarket(code)}
            className={`px-2 py-1 rounded text-[9px] font-mono uppercase border ${market === code ? "bg-white text-black border-white" : "text-zinc-400 border-white/10"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="max-h-44 overflow-y-auto rounded border border-white/10 bg-neutral-950 divide-y divide-white/5">
        {error && !symbols.length ? (
          <div className="p-3 text-[10px] font-mono text-amber-400">{error}</div>
        ) : filtered.length === 0 ? (
          <div className="p-3 text-[10px] font-mono text-zinc-500">No market matches "{q}".</div>
        ) : (
          filtered.map((s) => (
            <button
              type="button"
              key={s.symbol}
              onClick={() => onChange(s.symbol)}
              disabled={s.is_trading_suspended}
              className={`w-full text-left px-2.5 py-1.5 flex items-center justify-between text-[11px] font-mono hover:bg-white/5 disabled:opacity-40 ${
                s.symbol === value ? "bg-white/10 text-white" : "text-zinc-300"
              }`}
            >
              <span className="truncate">{s.display_name}</span>
              <span className="text-[9px] text-zinc-500 ml-2 shrink-0">
                {s.symbol}
                {!s.exchange_is_open && " · closed"}
                {s.is_trading_suspended && " · suspended"}
              </span>
            </button>
          ))
        )}
      </div>
      {current && (
        <div className="text-[9px] font-mono text-zinc-500">
          Selected: <span className="text-zinc-300">{current.display_name}</span> ({current.symbol})
        </div>
      )}
    </div>
  );
}
