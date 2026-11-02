import React, { useEffect, useRef, useState } from "react";
import { createChart, CandlestickSeries, ColorType, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";

interface Props {
  symbol: string;
  getHeaders: () => Promise<Record<string, string>>;
}

const TFS = ["1m", "5m", "15m", "1h", "4h", "1d"] as const;

// Native candlestick chart fed by Deriv's own candles
// (GET /api/brokers/deriv/candles). Works for every Deriv market,
// including the synthetics TradingView's free embed cannot chart.
export default function NativeChart({ symbol, getHeaders }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [tf, setTf] = useState<(typeof TFS)[number]>("15m");
  const [status, setStatus] = useState<string>("Loading candles...");

  useEffect(() => {
    if (!hostRef.current) return;
    const chart = createChart(hostRef.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#0a0a0a" }, textColor: "#a1a1aa" },
      grid: { vertLines: { color: "#18181b" }, horzLines: { color: "#18181b" } },
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#27272a" },
      rightPriceScale: { borderColor: "#27272a" },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });
    chartRef.current = chart;
    seriesRef.current = series;
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let first = true;
    const load = async () => {
      try {
        const res = await fetch(
          `/api/brokers/deriv/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${tf}&limit=400`,
          { headers: await getHeaders() }
        );
        if (!res.ok) {
          const b = await res.json().catch(() => ({}));
          throw new Error(b?.detail || `HTTP ${res.status}`);
        }
        const body = await res.json();
        if (cancelled || !seriesRef.current) return;
        seriesRef.current.setData(
          (body.candles || []).map((c: any) => ({ ...c, time: c.time as UTCTimestamp }))
        );
        if (first) {
          chartRef.current?.timeScale().fitContent();
          first = false;
        }
        setStatus("");
      } catch (e: any) {
        if (!cancelled) setStatus(`Chart unavailable: ${e?.message || e}`);
      }
    };
    setStatus("Loading candles...");
    void load();
    const timer = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol, tf]);

  return (
    <div className="relative w-full h-full flex flex-col">
      <div className="flex items-center gap-1 px-2 py-1.5 border-b border-white/5 bg-neutral-950">
        <span className="text-[10px] font-mono text-zinc-400 mr-2">{symbol}</span>
        {TFS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTf(t)}
            className={`px-2 py-0.5 rounded text-[10px] font-mono border ${tf === t ? "bg-white text-black border-white" : "text-zinc-400 border-white/10"}`}
          >
            {t}
          </button>
        ))}
      </div>
      <div ref={hostRef} className="flex-1 min-h-0" />
      {status && (
        <div className="absolute inset-0 top-8 flex items-center justify-center text-[11px] font-mono text-zinc-500 pointer-events-none">
          {status}
        </div>
      )}
    </div>
  );
}
