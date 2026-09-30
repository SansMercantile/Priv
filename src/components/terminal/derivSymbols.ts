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
