// Deriv symbol universe for the terminal: one cached fetch of the full
// active-symbol list (GET /api/brokers/deriv/symbols) shared by Order
// Dispatch, the chart and the Signals selector.

import { useEffect, useState } from "react";

export interface DerivSymbol {
  symbol: string;
  display_name: string;
  market: string;
  market_display_name: string;
  exchange_is_open: boolean;
  is_trading_suspended: boolean;
  pip?: number | null;
}

let cache: { at: number; list: DerivSymbol[] } | null = null;
let inflight: Promise<DerivSymbol[]> | null = null;
const TTL_MS = 10 * 60 * 1000;

export async function fetchDerivSymbols(headers: Record<string, string> = {}): Promise<DerivSymbol[]> {
  if (cache && Date.now() - cache.at < TTL_MS) return cache.list;
  if (inflight) return inflight;
  inflight = (async () => {
    try {
      const res = await fetch("/api/brokers/deriv/symbols", { headers });
      if (!res.ok) throw new Error(`symbols ${res.status}`);
      const body = await res.json();
      const list: DerivSymbol[] = (body?.symbols || []).filter((s: DerivSymbol) => !!s.symbol);
      if (list.length) cache = { at: Date.now(), list };
      return list;
    } finally {
      inflight = null;
    }
  })();
  return inflight;
}

export function useDerivSymbols(getHeaders?: () => Promise<Record<string, string>>) {
  const [symbols, setSymbols] = useState<DerivSymbol[]>(cache?.list || []);
  const [loading, setLoading] = useState(!cache);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = getHeaders ? await getHeaders() : {};
        const list = await fetchDerivSymbols(h);
        if (!cancelled) {
          setSymbols(list);
          setError(list.length ? null : "No symbols returned - Deriv connection may be offline.");
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Could not load Deriv symbols.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { symbols, loading, error };
}

const INDEX_TV: Record<string, string> = {
  OTC_DJI: "TVC:DJI",
  OTC_SPC: "SP:SPX",
  OTC_NDX: "NASDAQ:NDX",
  OTC_FTSE: "TVC:UKX",
  OTC_GDAXI: "XETR:DAX",
  OTC_N225: "TVC:NI225",
  OTC_HSI: "TVC:HSI",
};

/**
 * TradingView's free embed can chart mainstream markets (forex, crypto,
 * major indices, metals) but NOT Deriv's proprietary synthetic indices
 * (Volatility / Boom / Crash / Jump / Step ...). For those this returns
 * null and the terminal uses its native Deriv-candle chart instead of
 * silently pinning to BTCUSD like before.
 */
export function tvSymbolFor(code: string): string | null {
  if (!code) return null;
  if (INDEX_TV[code]) return INDEX_TV[code];
  let m = /^(?:frx|FRX)?([A-Z]{3})([A-Z]{3})$/.exec(code);
  if (m) {
    const pair = `${m[1]}${m[2]}`;
    if (["XAU", "XAG", "XPD", "XPT"].includes(m[1])) return `OANDA:${pair}`;
    return `FX_IDC:${pair}`;
  }
  m = /^(?:cry|CRY)([A-Z]+?)(USD|EUR|BTC|ETH)$/.exec(code);
  if (m) return `COINBASE:${m[1]}${m[2]}`;
  return null;
}

// Deriv's own Derived Indices feed on TradingView (DERIV: exchange,
// listed Jul 2026): Volatility / 1s Volatility / Boom / Crash / Jump /
// Step. Used only when the TradingView platform surface is active --
// elsewhere synthetics keep the native candle chart. A code that misses
// the table is recoverable: the TradingView platform embed leaves
// allow_symbol_change on so the widget's own search finds any symbol.
const DERIV_TV: Record<string, string> = {
  R_10: "DERIV:VOLATILITY_10_INDEX",
  R_25: "DERIV:VOLATILITY_25_INDEX",
  R_50: "DERIV:VOLATILITY_50_INDEX",
  R_75: "DERIV:VOLATILITY_75_INDEX",
  R_100: "DERIV:VOLATILITY_100_INDEX",
  "1HZ10V": "DERIV:VOLATILITY_10_1S_INDEX",
  "1HZ15V": "DERIV:VOLATILITY_15_1S_INDEX",
  "1HZ25V": "DERIV:VOLATILITY_25_1S_INDEX",
  "1HZ30V": "DERIV:VOLATILITY_30_1S_INDEX",
  "1HZ50V": "DERIV:VOLATILITY_50_1S_INDEX",
  "1HZ75V": "DERIV:VOLATILITY_75_1S_INDEX",
  "1HZ90V": "DERIV:VOLATILITY_90_1S_INDEX",
  "1HZ100V": "DERIV:VOLATILITY_100_1S_INDEX",
  BOOM500: "DERIV:BOOM_500_INDEX",
  BOOM1000: "DERIV:BOOM_1000_INDEX",
  CRASH500: "DERIV:CRASH_500_INDEX",
  CRASH1000: "DERIV:CRASH_1000_INDEX",
  JD10: "DERIV:JUMP_10_INDEX",
  JD25: "DERIV:JUMP_25_INDEX",
  JD50: "DERIV:JUMP_50_INDEX",
  JD75: "DERIV:JUMP_75_INDEX",
  JD100: "DERIV:JUMP_100_INDEX",
  stpRNG: "DERIV:STEP_INDEX",
};

/**
 * TV symbol for the terminal chart, aware of the selected platform.
 * TradingView surface: mainstream mapping first, then the DERIV:
 * synthetic feed, so the platform charts R_100 / BOOM / CRASH natively
 * "instead of the deriv charts" the native renderer draws. Any other
 * platform keeps the original behaviour (null -> native chart).
 */
export function tvSymbolForPlatform(code: string, platform?: string): string | null {
  const base = tvSymbolFor(code);
  if (base) return base;
  if ((platform || "").toLowerCase() === "tradingview") return DERIV_TV[code] || null;
  return null;
}
