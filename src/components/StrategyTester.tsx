import React, { useEffect, useMemo, useRef, useState } from "react";
import { FlaskConical, Play, RefreshCw, CheckCircle2, XCircle, Square, Star, History, ChevronDown } from "lucide-react";
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

// Sandbox board row: pin/label/note come from the persisted meta file,
// test stats are derived server-side from stored BacktestRun rows.
interface BoardRow {
  strategy: string;
  description?: string | null;
  category?: string | null;
  pinned?: boolean;
  label?: string | null;
  note?: string | null;
  last_tested_at?: string | null;
  tests?: number;
  best_return_pct?: number | null;
  avg_sharpe?: number | null;
}

// One persisted backtest row from GET /api/v1/backtest/runs.
interface RunRow {
  run_id: string;
  strategy: string;
  symbol: string;
  timeframe: string;
  total_return_pct?: number | null;
  sharpe?: number | null;
  win_rate?: number | null;
  num_trades?: number | null;
  created_at?: string | null;
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

// Backend timestamps are naive UTC -- assume Z when no zone present.
const parseUtc = (iso: string) =>
  new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);

// "just now" / "12m ago" / "3h ago" / "2d ago" / date for last-tested.
const fmtWhen = (iso?: string | null) => {
  if (!iso) return "never";
  const t = parseUtc(iso);
  if (Number.isNaN(t.getTime())) return "never";
  const sec = Math.max(0, (Date.now() - t.getTime()) / 1000);
  if (sec < 60) return "just now";
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  if (sec < 604800) return `${Math.floor(sec / 86400)}d ago`;
  return t.toLocaleDateString();
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

  // Main strategy (drives the server-side autotrader) + saved param tweaks.
  const [mainStrategy, setMainStrategy] = useState<string | null>(null);
  const [paramsMap, setParamsMap] = useState<Record<string, Record<string, any>>>({});
  const [paramDefaults, setParamDefaults] = useState<Record<string, Record<string, any>>>({});
  const [mainSaving, setMainSaving] = useState<string | null>(null);
  const [tweakFor, setTweakFor] = useState<string | null>(null);
  const [tweakDraft, setTweakDraft] = useState<Record<string, any>>({});
  const [tweakSaving, setTweakSaving] = useState(false);

  // Sandbox board: pins/labels/notes + real last-tested stats.
  const [boards, setBoards] = useState<BoardRow[]>([]);
  const [boardOpen, setBoardOpen] = useState(false);
  const [showAllBoards, setShowAllBoards] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editNote, setEditNote] = useState("");
  const [metaSaving, setMetaSaving] = useState(false);
  // Filterable persisted run history (shown while the board is open).
  const [histStrategy, setHistStrategy] = useState("all");
  const [histOutcome, setHistOutcome] = useState("all");
  const [history, setHistory] = useState<RunRow[] | null>(null);
  const [histLoading, setHistLoading] = useState(false);
  const [histError, setHistError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const [prof, sess, uni, brd, defs] = await Promise.allSettled([
        apiClient.get("/api/v1/profile/strategies"),
        apiClient.get("/api/v1/backtest/session-results"),
        apiClient.get("/api/v1/backtest/universe"),
        apiClient.get("/api/v1/backtest/sandbox/boards"),
        apiClient.get("/api/v1/backtest/strategies"),
      ]);
      if (cancelled) return;

      if (brd.status === "fulfilled") {
        const bs: BoardRow[] = brd.value?.data?.data?.boards ?? [];
        setBoards(bs);
        // Open the board by default only when something is pinned.
        if (bs.some((b) => b.pinned)) setBoardOpen(true);
      }

      let cat: Record<string, { description?: string; category?: string }> = {};
      if (prof.status === "fulfilled") {
        const d = prof.value?.data?.data;
        cat = d?.catalog ?? {};
        setCatalog(cat);
        setSelected(d?.selected ?? []);
        setMainStrategy(d?.main ?? null);
        setParamsMap(d?.params ?? {});
      }
      if (defs.status === "fulfilled") {
        const raw: Record<string, { defaults?: Record<string, any> }> = defs.value?.data?.data ?? {};
        const dm: Record<string, Record<string, any>> = {};
        for (const [name, spec] of Object.entries(raw)) dm[name] = spec?.defaults ?? {};
        setParamDefaults(dm);
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

  // Saved param tweaks travel with every run, so TEST / TEST ALL / the
  // sandbox bench exercise exactly what the autotrader will trade.
  const runParams = (name: string) => {
    const p = paramsMap[name];
    return p && Object.keys(p).length ? p : undefined;
  };

  const runOne = async (name: string) => {
    setSingleRunning(name);
    setActionError(null);
    try {
      const res: any = await apiClient.post("/api/v1/backtest/run", {
        symbol,
        timeframe,
        strategy: name,
        params: runParams(name)
      });
      const d = res?.data?.data;
      setLive((prev) => ({ ...prev, [name]: d ?? { ok: false, reason: "empty result" } }));
      // A persisted run bumps this strategy's real last-tested stat.
      loadBoards();
      if (boardOpen) loadHistory();
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
          strategy: name,
          params: runParams(name)
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

  const loadBoards = async () => {
    try {
      const res: any = await apiClient.get("/api/v1/backtest/sandbox/boards");
      setBoards(res?.data?.data?.boards ?? []);
    } catch {
      // Older backend without the boards endpoint: board stays hidden.
    }
  };

  const saveMeta = async (
    name: string,
    patch: { pinned?: boolean; label?: string; note?: string }
  ) => {
    setMetaSaving(true);
    setActionError(null);
    try {
      await apiClient.put("/api/v1/backtest/sandbox/meta", { strategy: name, ...patch });
      setEditing(null);
      await loadBoards();
    } catch (e: any) {
      setActionError(`Could not save sandbox meta: ${e?.message || "network error"}`);
    } finally {
      setMetaSaving(false);
    }
  };

  const loadHistory = async () => {
    setHistLoading(true);
    setHistError(null);
    try {
      const params = new URLSearchParams({ limit: "100" });
      if (histStrategy !== "all") params.set("strategy", histStrategy);
      if (histOutcome !== "all") params.set("outcome", histOutcome);
      const res: any = await apiClient.get(`/api/v1/backtest/runs?${params.toString()}`);
      setHistory(res?.data?.data ?? []);
    } catch (e: any) {
      setHistory(null);
      setHistError(e?.message || "could not load run history");
    } finally {
      setHistLoading(false);
    }
  };

  // Refetch whenever the board opens or a filter changes.
  useEffect(() => {
    if (boardOpen) loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [boardOpen, histStrategy, histOutcome]);

  const toggleUse = async (name: string) => {
    const already = selected.includes(name);
    const next = already ? selected.filter((s) => s !== name) : [...selected, name];
    const previous = selected;
    const previousMain = mainStrategy;
    setSelected(next);
    // Un-USEing the main strategy also clears MAIN (it no longer applies).
    if (already && mainStrategy === name) setMainStrategy(null);
    setSaving(name);
    setActionError(null);
    try {
      await apiClient.post("/api/v1/profile/strategies", { preferred_strategies: next });
      if (already && previousMain === name) {
        await apiClient.put("/api/v1/profile/strategies/main", { strategy: null });
      }
    } catch (e: any) {
      setSelected(previous);
      setMainStrategy(previousMain);
      setActionError(`Could not save your selection: ${e?.message || "network error"}`);
    } finally {
      setSaving(null);
    }
  };

  // Star a strategy as MAIN: the autotrader follows it while armed (and it
  // joins the selection pool server-side). Clicking the active star clears it.
  const setMain = async (name: string) => {
    const next = mainStrategy === name ? null : name;
    const previous = mainStrategy;
    setMainStrategy(next);
    setMainSaving(name);
    setActionError(null);
    try {
      await apiClient.put("/api/v1/profile/strategies/main", { strategy: next });
      if (next && !selected.includes(next)) setSelected((prev) => [...prev, next]);
    } catch (e: any) {
      setMainStrategy(previous);
      setActionError(`Could not save the main strategy: ${e?.message || "network error"}`);
    } finally {
      setMainSaving(null);
    }
  };

  // Param tweak editor: seeded from declared defaults + saved overrides.
  const openTweak = (name: string) => {
    setTweakDraft({ ...(paramDefaults[name] || {}), ...(paramsMap[name] || {}) });
    setTweakFor(name);
  };

  const saveTweak = async (name: string) => {
    const defaults = paramDefaults[name] || {};
    const cleaned: Record<string, any> = {};
    for (const [key, defVal] of Object.entries(defaults)) {
      const raw = tweakDraft[key];
      if (raw === undefined || raw === "") continue; // back to default
      if (typeof defVal === "number") {
        const n = Number(raw);
        if (!Number.isFinite(n)) {
          setActionError(`'${key}' must be a number.`);
          return;
        }
        cleaned[key] = Number.isInteger(defVal) ? Math.round(n) : n;
      } else {
        cleaned[key] = String(raw);
      }
    }
    setTweakSaving(true);
    setActionError(null);
    try {
      const res: any = await apiClient.put("/api/v1/profile/strategies/params", {
        strategy: name,
        params: cleaned
      });
      const saved = res?.data?.data?.params ?? cleaned;
      setParamsMap((prev) => {
        const next = { ...prev };
        if (Object.keys(saved).length) next[name] = saved;
        else delete next[name];
        return next;
      });
      setTweakFor(null);
    } catch (e: any) {
      setActionError(`Could not save tweaks: ${e?.message || "network error"}`);
    } finally {
      setTweakSaving(false);
    }
  };

  const clearTweak = async (name: string) => {
    setTweakSaving(true);
    setActionError(null);
    try {
      await apiClient.put("/api/v1/profile/strategies/params", { strategy: name, params: {} });
      setParamsMap((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
      setTweakFor(null);
    } catch (e: any) {
      setActionError(`Could not reset tweaks: ${e?.message || "network error"}`);
    } finally {
      setTweakSaving(false);
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
            Test every strategy from our engineering sessions against stored real market data, tweak
            their parameters, then USE the ones you are happy with. Star one as MAIN and the
            autotrader takes its trades exactly as tested.
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
                className={`inline-flex items-center gap-1.5 text-[10px] font-mono px-2.5 py-1 rounded-full border ${
                  mainStrategy === s
                    ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                    : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                }`}
              >
                {mainStrategy === s ? (
                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                ) : (
                  <CheckCircle2 className="w-3 h-3" />
                )}
                {s}
                {mainStrategy === s && <span className="font-bold">MAIN</span>}
                {paramsMap[s] && (
                  <span
                    title={`Tweaked params: ${JSON.stringify(paramsMap[s])}`}
                    className="text-[8.5px] px-1 rounded bg-white/10 text-zinc-300"
                  >
                    ~
                  </span>
                )}
              </span>
            ))}
          </div>
        )}
        {mainStrategy && (
          <p className="text-[10px] font-mono text-amber-300/80">
            ★ {mainStrategy} is MAIN — the autotrader follows this strategy (with your saved tweaks)
            while armed. Star another to switch, or click the star again to clear.
          </p>
        )}
        {!mainStrategy && selected.length > 0 && (
          <p className="text-[10px] font-mono text-zinc-500">
            No MAIN starred yet — the autotrader will use the first strategy in use (or the
            multi-agent desk). Star one below to pin it explicitly.
          </p>
        )}
        {actionError && (
          <p className="text-[11px] font-mono text-rose-400">{actionError}</p>
        )}
      </div>

      {/* Sandbox board: pinned/labelled strategies + real last-tested stats */}
      {boards.length > 0 && (
        <div className="space-y-3">
          <button
            onClick={() => setBoardOpen((o) => !o)}
            className="w-full flex items-center justify-between px-4 py-2.5 border border-white/10 rounded-xl bg-white/5 hover:bg-white/[0.08] transition cursor-pointer"
          >
            <span className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-bold">
              <Star className="w-3.5 h-3.5 text-amber-400" />
              Sandbox board
              <span className="text-zinc-600 normal-case font-normal">
                · {boards.filter((b) => b.pinned).length} pinned · {boards.length} strategies
              </span>
            </span>
            <ChevronDown
              className={`w-4 h-4 text-zinc-500 transition-transform ${boardOpen ? "rotate-180" : ""}`}
            />
          </button>

          {boardOpen && (
            <>
              <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
                {(() => {
                  const pinned = boards.filter((b) => b.pinned);
                  const unpinned = boards.filter((b) => !b.pinned);
                  const visible = showAllBoards
                    ? boards
                    : [...pinned, ...unpinned.slice(0, Math.max(0, 12 - pinned.length))];
                  return visible.map((b) => (
                    <div
                      key={b.strategy}
                      className={`p-3 border rounded-xl ${
                        b.pinned
                          ? "border-amber-500/40 bg-amber-500/[0.05]"
                          : "border-white/10 bg-black/30"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                              className="text-xs font-mono font-bold text-white truncate"
                              title={b.description ?? undefined}
                            >
                              {b.strategy}
                            </span>
                            {b.category && (
                              <span className="text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-zinc-500">
                                {b.category}
                              </span>
                            )}
                            {b.label && (
                              <span className="text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300">
                                {b.label}
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] font-mono text-zinc-500 mt-1">
                            <span
                              title={
                                b.last_tested_at
                                  ? `Last tested ${parseUtc(b.last_tested_at).toLocaleString()}`
                                  : "No stored runs yet"
                              }
                              className={b.last_tested_at ? "" : "text-zinc-600"}
                            >
                              tested {fmtWhen(b.last_tested_at)}
                            </span>
                            <span className="text-zinc-600"> · {b.tests ?? 0} runs</span>
                            {b.best_return_pct != null && (
                              <span className={b.best_return_pct >= 0 ? "text-emerald-500/80" : "text-rose-400/80"}>
                                {" "}· best {fmtPct(b.best_return_pct)}
                              </span>
                            )}
                            {b.avg_sharpe != null && (
                              <span className="text-zinc-600"> · sh {fmtNum(b.avg_sharpe)}</span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => saveMeta(b.strategy, { pinned: !b.pinned })}
                          disabled={metaSaving}
                          title={b.pinned ? "Unpin from board" : "Pin to board"}
                          className="shrink-0 p-1 rounded hover:bg-white/10 transition disabled:opacity-40 cursor-pointer"
                        >
                          <Star
                            className={`w-4 h-4 ${b.pinned ? "text-amber-400 fill-amber-400" : "text-zinc-600"}`}
                          />
                        </button>
                      </div>

                      {editing === b.strategy ? (
                        <div className="mt-2 space-y-1.5">
                          <input
                            value={editLabel}
                            onChange={(e) => setEditLabel(e.target.value)}
                            maxLength={60}
                            placeholder="Label (e.g. A-grade trend)"
                            className="w-full bg-neutral-950 border border-white/15 rounded px-2 py-1.5 text-[11px] font-mono text-white focus:outline-none focus:border-white/40"
                          />
                          <textarea
                            value={editNote}
                            onChange={(e) => setEditNote(e.target.value)}
                            maxLength={2000}
                            rows={3}
                            placeholder="Notes: why it works, market conditions, what to watch..."
                            className="w-full bg-neutral-950 border border-white/15 rounded px-2 py-1.5 text-[11px] font-mono text-white focus:outline-none focus:border-white/40 resize-y"
                          />
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => saveMeta(b.strategy, { label: editLabel, note: editNote })}
                              disabled={metaSaving}
                              className="px-2.5 py-1 rounded border border-emerald-500/40 bg-emerald-500/15 text-emerald-300 text-[9.5px] font-mono font-bold disabled:opacity-40 cursor-pointer"
                            >
                              {metaSaving ? "SAVING..." : "SAVE"}
                            </button>
                            <button
                              onClick={() => setEditing(null)}
                              className="px-2.5 py-1 rounded border border-white/15 text-zinc-400 text-[9.5px] font-mono font-bold hover:bg-white/10 cursor-pointer"
                            >
                              CANCEL
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-2 flex items-start justify-between gap-2">
                          <p
                            className="text-[10.5px] text-zinc-500 font-mono leading-snug truncate flex-1"
                            title={b.note ?? ""}
                          >
                            {b.note || <span className="text-zinc-600">no notes</span>}
                          </p>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <button
                              onClick={() => {
                                setEditing(b.strategy);
                                setEditLabel(b.label ?? "");
                                setEditNote(b.note ?? "");
                              }}
                              className="px-2 py-1 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-[9.5px] font-mono font-bold text-zinc-300 transition cursor-pointer"
                            >
                              EDIT
                            </button>
                            <button
                              onClick={() => runOne(b.strategy)}
                              disabled={testing || singleRunning !== null}
                              title={`Run on ${symbol} ${timeframe}`}
                              className="px-2 py-1 rounded border border-white/15 bg-white/5 hover:bg-white/10 text-[9.5px] font-mono font-bold text-white transition disabled:opacity-40 cursor-pointer"
                            >
                              {singleRunning === b.strategy ? "..." : "TEST"}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ));
                })()}
              </div>

              {boards.length > 12 && (
                <button
                  onClick={() => setShowAllBoards((v) => !v)}
                  className="w-full py-2 rounded border border-white/10 bg-white/5 hover:bg-white/10 text-[10px] font-mono font-bold text-zinc-400 transition cursor-pointer"
                >
                  {showAllBoards ? "SHOW FEWER" : `SHOW ALL ${boards.length} STRATEGIES`}
                </button>
              )}

              {/* Filterable persisted test history */}
              <div className="border border-white/10 rounded-xl overflow-hidden">
                <div className="px-4 py-2.5 bg-white/5 flex flex-wrap items-center gap-2">
                  <span className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                    <History className="w-3.5 h-3.5" />
                    Test history
                    <span className="text-zinc-600 normal-case font-normal">
                      (stored backtests)
                    </span>
                  </span>
                  <div className="ml-auto flex items-center gap-2">
                    <select
                      value={histStrategy}
                      onChange={(e) => setHistStrategy(e.target.value)}
                      className="bg-neutral-950 border border-white/10 rounded px-2 py-1 text-[10px] font-mono text-white focus:outline-none focus:border-white/30 cursor-pointer"
                      title="Filter by strategy"
                    >
                      <option value="all">All strategies</option>
                      {boards.map((b) => (
                        <option key={b.strategy} value={b.strategy}>
                          {b.strategy}
                        </option>
                      ))}
                    </select>
                    <select
                      value={histOutcome}
                      onChange={(e) => setHistOutcome(e.target.value)}
                      className="bg-neutral-950 border border-white/10 rounded px-2 py-1 text-[10px] font-mono text-white focus:outline-none focus:border-white/30 cursor-pointer"
                      title="Filter by outcome"
                    >
                      <option value="all">Any outcome</option>
                      <option value="profit">Profit only</option>
                      <option value="loss">Loss only</option>
                    </select>
                    <button
                      onClick={loadHistory}
                      disabled={histLoading}
                      title="Refresh history"
                      className="p-1.5 rounded border border-white/10 bg-white/5 hover:bg-white/10 transition disabled:opacity-40 cursor-pointer"
                    >
                      <RefreshCw className={`w-3 h-3 text-zinc-400 ${histLoading ? "animate-spin" : ""}`} />
                    </button>
                  </div>
                </div>
                {histError && (
                  <p className="px-4 py-2 text-[11px] font-mono text-rose-400">{histError}</p>
                )}
                <div className="max-h-80 overflow-y-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[9px] font-mono">
                        <th className="py-1.5 px-3">When</th>
                        <th className="py-1.5 px-3">Strategy</th>
                        <th className="py-1.5 px-3">Symbol</th>
                        <th className="py-1.5 px-3">TF</th>
                        <th className="py-1.5 px-3 text-right">Return</th>
                        <th className="py-1.5 px-3 text-right">Sharpe</th>
                        <th className="py-1.5 px-3 text-right">Win</th>
                        <th className="py-1.5 px-3 text-right">Trades</th>
                        <th className="py-1.5 px-3">Run</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history?.map((r) => (
                        <tr key={r.run_id} className="border-t border-white/5 hover:bg-white/[0.03]">
                          <td
                            className="py-1.5 px-3 text-[9.5px] font-mono text-zinc-500 whitespace-nowrap"
                            title={r.created_at ? parseUtc(r.created_at).toLocaleString() : ""}
                          >
                            {r.created_at ? fmtWhen(r.created_at) : "—"}
                          </td>
                          <td className="py-1.5 px-3 text-[10px] font-mono font-bold text-white">
                            {r.strategy}
                          </td>
                          <td className="py-1.5 px-3 text-[10px] font-mono text-zinc-400">{r.symbol}</td>
                          <td className="py-1.5 px-3 text-[10px] font-mono text-zinc-500">{r.timeframe}</td>
                          <td
                            className={`py-1.5 px-3 text-right text-[10px] font-mono ${
                              (r.total_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"
                            }`}
                          >
                            {fmtPct(r.total_return_pct)}
                          </td>
                          <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                            {fmtNum(r.sharpe)}
                          </td>
                          <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                            {fmtWin(r.win_rate)}
                          </td>
                          <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                            {r.num_trades ?? "—"}
                          </td>
                          <td
                            className="py-1.5 px-3 text-[9px] font-mono text-zinc-600 truncate max-w-[160px]"
                            title={r.run_id}
                          >
                            {r.run_id}
                          </td>
                        </tr>
                      ))}
                      {histLoading && !history && !histError && (
                        <tr>
                          <td colSpan={9} className="py-6 text-center text-[10px] font-mono text-zinc-500">
                            LOADING HISTORY...
                          </td>
                        </tr>
                      )}
                      {history?.length === 0 && !histLoading && (
                        <tr>
                          <td colSpan={9} className="py-6 text-center text-[10px] font-mono text-zinc-500">
                            No runs match these filters — press TEST on a card to create one.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

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
                const isMain = mainStrategy === r.name;
                const isTweaked = !!paramsMap[r.name];
                const defs = paramDefaults[r.name] || {};
                return (
                  <React.Fragment key={r.name}>
                  <tr
                    className={`border-t border-white/5 hover:bg-white/[0.03] ${
                      isMain ? "bg-amber-500/[0.05]" : isSelected ? "bg-emerald-500/[0.04]" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3 text-[10px] font-mono text-zinc-600">{idx + 1}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white">{r.name}</span>
                        {isMain && (
                          <span
                            title="MAIN — the autotrader follows this strategy"
                            className="inline-flex items-center gap-1 text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-300 font-bold"
                          >
                            <Star className="w-2.5 h-2.5 fill-amber-400" /> MAIN
                          </span>
                        )}
                        {r.stats?.category && (
                          <span className="text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-white/10 bg-white/5 text-zinc-500">
                            {r.stats.category}
                          </span>
                        )}
                        {isTweaked && (
                          <span
                            title={`Param tweaks saved: ${JSON.stringify(paramsMap[r.name])}`}
                            className="text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded border border-sky-500/40 bg-sky-500/10 text-sky-300"
                          >
                            tweaked
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
                          onClick={() => (tweakFor === r.name ? setTweakFor(null) : openTweak(r.name))}
                          disabled={tweakSaving}
                          title="Tweak this strategy's parameters (saved and used by TEST runs + the autotrader)"
                          className={`px-2.5 py-1 rounded border text-[9.5px] font-mono font-bold transition disabled:opacity-40 cursor-pointer ${
                            tweakFor === r.name
                              ? "border-sky-500/40 bg-sky-500/15 text-sky-300"
                              : "border-white/15 bg-white/5 hover:bg-white/10 text-white"
                          }`}
                        >
                          {isTweaked ? "PARAMS ~" : "PARAMS"}
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
                        <button
                          onClick={() => setMain(r.name)}
                          disabled={mainSaving !== null || (!isSelected && !isMain)}
                          title={
                            isMain
                              ? "MAIN — click to clear (autotrader falls back to first in use / multi-agent desk)"
                              : isSelected
                              ? "Star as MAIN — the autotrader follows this strategy"
                              : "Press USE first, then star as MAIN"
                          }
                          className={`px-2.5 py-1 rounded border text-[9.5px] font-mono font-bold transition disabled:opacity-40 cursor-pointer ${
                            isMain
                              ? "border-amber-500/50 bg-amber-500/15 text-amber-300"
                              : "border-white/15 bg-white/5 hover:bg-white/10 text-zinc-300"
                          }`}
                        >
                          {mainSaving === r.name ? "..." : isMain ? "★ MAIN" : "☆ MAIN"}
                        </button>
                      </div>
                    </td>
                  </tr>

                  {/* Param tweak editor (expandable row) */}
                  {tweakFor === r.name && (
                    <tr className="border-t border-white/5 bg-white/[0.02]">
                      <td colSpan={7} className="px-3 py-3">
                        <div className="space-y-2.5">
                          <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                            Tweak params — {r.name}
                            <span className="text-zinc-600 normal-case font-normal">
                              {" "}· saved tweaks drive TEST runs and the autotrader; blank = default
                            </span>
                          </div>
                          {Object.keys(defs).length > 0 ? (
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                              {Object.entries(defs).map(([key, defVal]) => (
                                <label
                                  key={key}
                                  className="flex flex-col gap-1 text-[9.5px] font-mono text-zinc-400"
                                >
                                  <span className="flex items-center justify-between">
                                    {key}
                                    {String(tweakDraft[key] ?? "") !== String(defVal) && (
                                      <span className="text-sky-400">edited</span>
                                    )}
                                  </span>
                                  <input
                                    value={String(tweakDraft[key] ?? "")}
                                    onChange={(e) =>
                                      setTweakDraft((d) => ({ ...d, [key]: e.target.value }))
                                    }
                                    placeholder={`default: ${String(defVal)}`}
                                    className="bg-neutral-950 border border-white/15 rounded px-2 py-1 text-[11px] font-mono text-white focus:outline-none focus:border-white/40"
                                  />
                                </label>
                              ))}
                            </div>
                          ) : (
                            <p className="text-[10px] font-mono text-zinc-500">
                              No tunable params declared for this strategy.
                            </p>
                          )}
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <button
                              onClick={() => saveTweak(r.name)}
                              disabled={tweakSaving}
                              className="px-2.5 py-1 rounded border border-emerald-500/40 bg-emerald-500/15 text-emerald-300 text-[9.5px] font-mono font-bold disabled:opacity-40 cursor-pointer"
                            >
                              {tweakSaving ? "SAVING..." : "SAVE TWEAKS"}
                            </button>
                            <button
                              onClick={() => clearTweak(r.name)}
                              disabled={tweakSaving || !isTweaked}
                              className="px-2.5 py-1 rounded border border-white/15 text-zinc-400 text-[9.5px] font-mono font-bold hover:bg-white/10 disabled:opacity-40 cursor-pointer"
                            >
                              RESET TO DEFAULTS
                            </button>
                            <button
                              onClick={() => setTweakFor(null)}
                              className="px-2.5 py-1 rounded border border-white/15 text-zinc-400 text-[9.5px] font-mono font-bold hover:bg-white/10 cursor-pointer"
                            >
                              CLOSE
                            </button>
                            {isTweaked && (
                              <span className="text-[9.5px] font-mono text-sky-300">
                                active: {JSON.stringify(paramsMap[r.name])}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                  </React.Fragment>
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
