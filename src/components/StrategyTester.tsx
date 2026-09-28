import React, { useEffect, useMemo, useRef, useState } from "react";
import { FlaskConical, Play, RefreshCw, CheckCircle2, XCircle, Square } from "lucide-react";
import apiClient from "../api/apiClient";

interface StratStats {
  category?: string;
  description?: string;
  avg_return_pct?: number;
  avg_sharpe?: number;
  total_trades?: number;
  num_symbols_profitable?: number;
  total_symbols_tested?: number;
}

interface LiveResult {
  ok?: boolean;
  total_return_pct?: number;
  sharpe?: number;
  win_rate?: number;
  num_trades?: number;
  max_drawdown_pct?: number;
  elapsed_sec?: number;
  reason?: string;
}

const fmtPct = (v?: number) =>
  v === undefined || v === null || Number.isNaN(v) ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(v >= 100 ? 0 : 2)}%`;
const fmtNum = (v?: number, d = 2) =>
  v === undefined || v === null || Number.isNaN(v) ? "—" : v.toFixed(d);
// run_backtest has reported win_rate as both a fraction and a percent
// across producers -- normalize for display only.
const fmtWin = (v?: number) => {
  if (v === undefined || v === null || Number.isNaN(v)) return "—";
  const pct = v <= 1 ? v * 100 : v;
  return `${pct.toFixed(1)}%`;
};

// Strategy Tester -- the Strategies page's testing bench. Built on the
// strategy-test sessions run during our engineering sessions: 44
// strategies over real data (all_strategies_real_data_results.json via
// GET /api/v1/backtest/session-results), plus fresh runs against stored
// history (POST /api/v1/backtest/run) and direct selection of the
// strategy(s) the user is happy with (their choice persists server-side
// in the profile and is reused across Priv).
export default function StrategyTester() {
  const [catalog, setCatalog] = useState<Record<string, { description?: string; category?: string }>>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [session, setSession] = useState<any>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("1d");

  const [live, setLive] = useState<Record<string, LiveResult>>({});
  const [singleRunning, setSingleRunning] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [progress, setProgress] = useState<{ done: number; total: number; current: string } | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const abortRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const [prof, sess, uni] = await Promise.allSettled([
        apiClient.get("/api/v1/profile/strategies"),
        apiClient.get("/api/v1/backtest/session-results"),
        apiClient.get("/api/v1/backtest/universe"),
      ]);
      if (cancelled) return;

      let cat: Record<string, { description?: string; category?: string }> = {};
      if (prof.status === "fulfilled") {
        const d = prof.value?.data?.data;
        cat = d?.catalog ?? {};
        setCatalog(cat);
        setSelected(d?.selected ?? []);
      }
      if (sess.status === "fulfilled") {
        setSession(sess.value?.data?.data ?? null);
      }
      const universeSyms: string[] =
        uni.status === "fulfilled"
          ? Array.from(
              new Set(
                ((uni.value?.data?.data?.classes ?? []) as any[]).flatMap(
                  (c) => c.symbols_with_data ?? []
                )
              )
            )
          : [];
      // Prefer symbols proven in the session artifacts, intersected with
      // current coverage; fall back to any covered symbol.
      const sessionSyms: string[] = sess.status === "fulfilled" ? sess.value?.data?.data?.symbol_best ?? [] : [];
      const sessionKeys = Object.keys(
        sess.status === "fulfilled" ? sess.value?.data?.data?.symbol_best ?? {} : {}
      );
      const pool = universeSyms.length ? universeSyms : sessionKeys;
      const preferred = sessionKeys.filter((s) => pool.includes(s));
      const ordered = [...new Set([...preferred, ...pool])];
      setSymbols(ordered);
      setSymbol((prev) => prev || ordered[0] || "AAPL");

      if (prof.status === "rejected" && sess.status === "rejected") {
        setLoadError("Could not load strategy data from the backend.");
      }
      setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Rankings from the session artifacts first (tested order), then any
  // catalog-only strategies the sessions didn't reach.
  const rows = useMemo(() => {
    const map = new Map<string, StratStats>();
    if (Array.isArray(session?.strategy_rankings)) {
      for (const pair of session.strategy_rankings) {
        if (Array.isArray(pair) && pair[0]) map.set(String(pair[0]), (pair[1] as StratStats) ?? {});
      }
    }
    for (const [name, meta] of Object.entries(catalog)) {
      if (!map.has(name)) map.set(name, { category: meta?.category, description: meta?.description });
    }
    return Array.from(map, ([name, stats]) => ({ name, stats }));
  }, [session, catalog]);

  const runOne = async (name: string) => {
    setSingleRunning(name);
    setActionError(null);
    try {
      const res: any = await apiClient.post("/api/v1/backtest/run", {
        symbol,
        timeframe,
        strategy: name
      });
      const d = res?.data?.data;
      setLive((prev) => ({ ...prev, [name]: d ?? { ok: false, reason: "empty result" } }));
    } catch (e: any) {
      setLive((prev) => ({ ...prev, [name]: { ok: false, reason: e?.message || "run failed" } }));
    } finally {
      setSingleRunning(null);
    }
  };

  const runAll = async () => {
    if (testing) {
      abortRef.current = true;
      return;
    }
    if (!rows.length) return;
    abortRef.current = false;
    setTesting(true);
    setActionError(null);
    const names = rows.map((r) => r.name);
    for (let i = 0; i < names.length; i++) {
      if (abortRef.current) break;
      const name = names[i];
      setProgress({ done: i, total: names.length, current: name });
      try {
        const res: any = await apiClient.post("/api/v1/backtest/run", {
          symbol,
          timeframe,
          strategy: name
        });
        setLive((prev) => ({ ...prev, [name]: res?.data?.data ?? { ok: false, reason: "empty result" } }));
      } catch (e: any) {
        setLive((prev) => ({
          ...prev,
          [name]: { ok: false, reason: e?.message || "run failed" }
        }));
      }
    }
    setProgress(null);
    setTesting(false);
  };

  const toggleUse = async (name: string) => {
    const already = selected.includes(name);
    const next = already ? selected.filter((s) => s !== name) : [...selected, name];
    const previous = selected;
    setSelected(next);
    setSaving(name);
    setActionError(null);
    try {
      await apiClient.post("/api/v1/profile/strategies", { preferred_strategies: next });
    } catch (e: any) {
      setSelected(previous);
      setActionError(`Could not save your selection: ${e?.message || "network error"}`);
    } finally {
      setSaving(null);
    }
  };

  const sessionDate = session?.timestamp ? new Date(session.timestamp) : null;

  if (loading) {
    return (
      <div className="flex items-center gap-3 text-zinc-400 font-mono text-xs py-10">
        <RefreshCw className="w-4 h-4 animate-spin text-rose-500" />
        LOADING STRATEGY SESSION DATA...
      </div>
    );
  }

  if (loadError && !rows.length) {
    return (
      <div className="p-5 border border-rose-900/40 bg-rose-950/10 rounded-xl text-xs font-mono text-rose-300">
        {loadError}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal flex items-center">
            <FlaskConical className="w-7 h-7 mr-3 text-white/70" />
            Strategy Tester
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            Test every strategy from our engineering sessions against stored real market data, then USE
            the ones you are happy with -- your selection stays active across Priv.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2">
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-white/30 cursor-pointer"
              title="Symbol to test against"
            >
              {symbols.length === 0 && <option value={symbol || "AAPL"}>{symbol || "AAPL"}</option>}
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="bg-neutral-950 border border-white/10 rounded px-2.5 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-white/30 cursor-pointer"
              title="Timeframe"
            >
              {["1d", "4h", "1h", "1w"].map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={runAll}
            className={`flex items-center gap-2 px-4 py-2 rounded font-mono text-xs font-bold border transition cursor-pointer ${
              testing
                ? "bg-rose-950/40 border-rose-500/40 text-rose-300"
                : "bg-white text-black border-white hover:bg-neutral-200"
            }`}
          >
            {testing ? (
              <>
                <Square className="w-3.5 h-3.5" /> STOP ({progress ? `${progress.done}/${progress.total}` : "..."})
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-black" /> TEST ALL ({rows.length})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Session metadata chips */}
      <div className="flex flex-wrap gap-2">
        {[
          sessionDate && `Session ${sessionDate.toISOString().slice(0, 10)}`,
          session?.total_strategies && `${session.total_strategies} strategies tested`,
          Array.isArray(session?.symbols_tested) && `${session.symbols_tested.length} symbols`,
          session?.total_simulations && `${session.total_simulations.toLocaleString("en-US")} simulations`,
          session?.total_duration_sec && `${Math.round(session.total_duration_sec)}s compute`
        ]
          .filter(Boolean)
          .map((chip, i) => (
            <span
              key={i}
              className="text-[10px] font-mono px-2 py-1 rounded border border-white/10 bg-white/5 text-zinc-400"
            >
              {String(chip)}
            </span>
          ))}
        {testing && progress && (
          <span className="text-[10px] font-mono px-2 py-1 rounded border border-rose-500/30 bg-rose-950/30 text-rose-300 animate-pulse">
            TESTING {progress.current} — {progress.done}/{progress.total}
          </span>
        )}
      </div>

      {/* In-use selection */}
      <div className="p-4 border border-white/10 rounded-xl bg-black/30 space-y-2.5">
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          Strategies in use
        </div>
        {selected.length === 0 ? (
          <p className="text-xs text-zinc-500 font-mono">
            None selected yet — press USE on any strategy you are happy with to make it active.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {selected.map((s) => (
              <span
                key={s}
                className="inline-flex items-center gap-1.5 text-[10px] font-mono px-2.5 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
              >
                <CheckCircle2 className="w-3 h-3" />
                {s}
              </span>
            ))}
          </div>
        )}
        {actionError && (
          <p className="text-[11px] font-mono text-rose-400">{actionError}</p>
        )}
      </div>

      {/* Results table */}
      <div className="border border-white/10 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 text-zinc-500 uppercase text-[9px] font-mono">
                <th className="py-2.5 px-3 w-8">#</th>
                <th className="py-2.5 px-3">Strategy</th>
                <th className="py-2.5 px-3 text-right">Session Avg Return</th>
                <th className="py-2.5 px-3 text-right">Avg Sharpe</th>
                <th className="py-2.5 px-3 text-right">Profitable Symbols</th>
                <th className="py-2.5 px-3 text-right">Live Test</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, idx) => {
                const res = live[r.name];
                const isSelected = selected.includes(r.name);
                const isTesting = singleRunning === r.name;
                return (
                  <tr
                    key={r.name}
                    className={`border-t border-white/5 hover:bg-white/[0.03] ${
                      isSelected ? "bg-emerald-500/[0.04]" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3 text-[10px] font-mono text-zinc-600">{idx + 1}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white">{r.name}</span>
                        {r.stats?.category && (
                          <span className="text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-zinc-500">
                            {r.stats.category}
                          </span>
                        )}
                      </div>
                      {r.stats?.description && (
                        <div className="text-[10px] text-zinc-500 mt-0.5 max-w-md truncate" title={r.stats.description}>
                          {r.stats.description}
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right text-xs font-mono text-white">
                      {fmtPct(r.stats?.avg_return_pct)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-xs font-mono text-zinc-400">
                      {fmtNum(r.stats?.avg_sharpe)}
                    </td>
                    <td className="py-2.5 px-3 text-right text-[11px] font-mono text-zinc-400">
                      {r.stats?.num_symbols_profitable !== undefined
                        ? `${r.stats.num_symbols_profitable}/${r.stats.total_symbols_tested}`
                        : "—"}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {res ? (
                        res.ok === false || (res.reason && res.total_return_pct === undefined) ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-rose-400" title={res.reason}>
                            <XCircle className="w-3 h-3" />
                            {res.reason ? res.reason.slice(0, 24) : "FAILED"}
                          </span>
                        ) : (
                          <div className="text-[10.5px] font-mono leading-tight">
                            <span className={((res.total_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400") + " font-bold"}>
                              {fmtPct(res.total_return_pct)}
                            </span>
                            <span className="text-zinc-500"> · sh {fmtNum(res.sharpe)}</span>
                            <span className="text-zinc-600 block">wr {fmtWin(res.win_rate)} · {res.num_trades ?? "—"} trades</span>
                          </div>
                        )
                      ) : (
                        <span className="text-zinc-600 text-[10px] font-mono">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <button
                          onClick={() => runOne(r.name)}
                          disabled={testing || singleRunning !== null}
                          title={`Run on ${symbol} ${timeframe}`}
                          className="px-2.5 py-1 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-[9.5px] font-mono font-bold text-white transition disabled:opacity-40 cursor-pointer"
                        >
                          {isTesting ? "RUNNING..." : "TEST"}
                        </button>
                        <button
                          onClick={() => toggleUse(r.name)}
                          disabled={saving !== null}
                          className={`px-2.5 py-1 rounded border text-[9.5px] font-mono font-bold transition disabled:opacity-40 cursor-pointer ${
                            isSelected
                              ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                              : "border-white/15 bg-white text-black hover:bg-neutral-200"
                          }`}
                        >
                          {saving === r.name ? "SAVING..." : isSelected ? "✓ IN USE" : "USE"}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs font-mono text-zinc-500">
                    No strategies available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Session run log */}
      {Array.isArray(session?.recent_runs) && session.recent_runs.length > 0 && (
        <div className="border border-white/10 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-white/5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold flex items-center gap-2">
            <FlaskConical className="w-3.5 h-3.5" />
            Session run log ({session.recent_runs.length} stored runs)
          </div>
          <div className="max-h-64 overflow-y-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[9px] font-mono sticky top-0 bg-zinc-950">
                  <th className="py-1.5 px-3">Run</th>
                  <th className="py-1.5 px-3">Strategy</th>
                  <th className="py-1.5 px-3">Symbol</th>
                  <th className="py-1.5 px-3 text-right">Return</th>
                  <th className="py-1.5 px-3 text-right">Sharpe</th>
                  <th className="py-1.5 px-3 text-right">Win Rate</th>
                  <th className="py-1.5 px-3 text-right">Trades</th>
                </tr>
              </thead>
              <tbody>
                {session.recent_runs.map((run: any, i: number) => (
                  <tr key={run.run_id || i} className="border-t border-white/5 hover:bg-white/[0.03]">
                    <td className="py-1.5 px-3 text-[9.5px] font-mono text-zinc-600 truncate max-w-[180px]">
                      {run.run_id || i + 1}
                    </td>
                    <td className="py-1.5 px-3 text-[10px] font-mono font-bold text-white">{run.strategy}</td>
                    <td className="py-1.5 px-3 text-[10px] font-mono text-zinc-400">{run.symbol}</td>
                    <td className={`py-1.5 px-3 text-right text-[10px] font-mono ${(run.total_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {fmtPct(run.total_return_pct)}
                    </td>
                    <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">{fmtNum(run.sharpe)}</td>
                    <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">{fmtWin(run.win_rate)}</td>
                    <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">{run.num_trades ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
