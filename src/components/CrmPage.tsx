import React, { useEffect, useMemo, useState } from "react";
import { Users, RefreshCw, Search, X, Plus, AlertTriangle, CheckCircle2 } from "lucide-react";
import apiClient from "../api/apiClient";

// Admin Client CRM -- ported from the ptah-realty CRM design (KPI strip,
// search/filter bar, master-detail table, tabbed detail modal) and fed
// exclusively by the existing admin endpoints:
//   GET    /api/v1/admin/clients               (subscription rows)
//   GET    /api/v1/admin/clients/{id}          (invoices + billing history)
//   POST   /api/v1/admin/clients               (manual onboard)
//   POST   /api/v1/admin/clients/{id}/plan     (plan override)
//   POST   /api/v1/admin/clients/{id}/fix      (stuck-account fixes)
//   DELETE /api/v1/admin/clients/{id}
//   GET    /api/v1/admin/trading/overview      (identity/trading/license merge)
//   PUT    /api/v1/admin/licenses/{id}         (node license)
//   GET    /api/v1/payment/plans               (plan catalogue)
// Route is wrapped in RequireAdmin (App.tsx); sidebar hides it from clients.

interface ClientSub {
  user_id: string;
  subscription_id?: string | null;
  plan_id?: string | null;
  plan_name?: string | null;
  status?: string | null;
  payment_provider?: string | null;
  current_period_end?: string | null;
  created_at?: string | null;
}

interface OverviewAccount {
  adapter_id: string;
  account_id: string;
  balance?: number | null;
  currency?: string | null;
  open_count?: number;
  open_stake_total?: number;
  open_positions?: Array<{
    order_id?: string;
    symbol?: string;
    contract_type?: string;
    stake?: number;
    payout?: number;
  }>;
}

interface OverviewUser {
  user_id: string;
  name?: string | null;
  email?: string | null;
  kyc_status?: string | null;
  plan?: string | null;
  subscription_status?: string | null;
  license?: { tier?: string; enabled?: boolean };
  accounts?: OverviewAccount[];
  signals_30d?: number;
  signals_open?: number;
  sources?: string[];
}

interface PlanOpt {
  plan_id: string;
  name: string;
  price?: number;
  currency?: string;
}

interface MergedRow extends ClientSub {
  name?: string | null;
  email?: string | null;
  kyc?: string | null;
  license?: { tier?: string; enabled?: boolean };
  accounts?: OverviewAccount[];
  signals_30d?: number;
  signals_open?: number;
  sources?: string[];
}

interface ClientDetail {
  subscription?: Record<string, any> | null;
  invoices?: Array<Record<string, any>>;
  billing_history?: Array<Record<string, any>>;
}

// Backend timestamps are naive UTC -- assume Z when no zone present.
const parseUtc = (iso: string) =>
  new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`);
const fmtDate = (iso?: string | null) => {
  if (!iso) return "—";
  const t = parseUtc(iso);
  return Number.isNaN(t.getTime()) ? "—" : t.toLocaleDateString();
};
const fmtDateTime = (iso?: string | null) => {
  if (!iso) return "—";
  const t = parseUtc(iso);
  return Number.isNaN(t.getTime()) ? "—" : t.toLocaleString();
};
const fmtNum = (v?: number | null, d = 2) =>
  v === undefined || v === null || Number.isNaN(Number(v)) ? "—" : Number(v).toFixed(d);

const statusBadge = (s?: string | null) => {
  const v = (s || "").toLowerCase();
  if (v === "active" || v === "paid" || v === "succeeded" || v === "open")
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-300";
  if (v === "cancelled" || v === "canceled" || v === "failed" || v === "void")
    return "border-rose-500/40 bg-rose-500/10 text-rose-300";
  if (v === "past_due" || v === "overdue" || v === "uncollectible")
    return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  if (v === "pending" || v === "trialing" || v === "draft")
    return "border-sky-500/40 bg-sky-500/10 text-sky-300";
  return "border-white/15 bg-white/5 text-zinc-400";
};

const planBadge = (p?: string | null) => {
  if (!p) return "border-white/10 bg-white/5 text-zinc-500";
  const v = p.toLowerCase();
  if (v === "free") return "border-white/15 bg-white/5 text-zinc-400";
  if (v === "autonomous" || v === "sovereign") return "border-amber-500/40 bg-amber-500/10 text-amber-300";
  return "border-violet-500/40 bg-violet-500/10 text-violet-300";
};

const FIX_ACTIONS = [
  { id: "reactivate", label: "Reactivate (reset status, clear cancel)" },
  { id: "clear_cancellation", label: "Clear cancellation flag" },
  { id: "reset_status_active", label: "Reset status → active" },
];

export default function CrmPage() {
  const [clients, setClients] = useState<ClientSub[]>([]);
  const [overview, setOverview] = useState<OverviewUser[]>([]);
  const [plans, setPlans] = useState<PlanOpt[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [search, setSearch] = useState("");
  const [planFilter, setPlanFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [modal, setModal] = useState<null | "detail" | "new">(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "billing" | "actions">("overview");
  const [detail, setDetail] = useState<ClientDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const [licTier, setLicTier] = useState("standard");
  const [licEnabled, setLicEnabled] = useState(true);
  const [setPlanName, setSetPlanName] = useState("");
  const [setPlanReason, setSetPlanReason] = useState("");
  const [fixAction, setFixAction] = useState("reactivate");
  const [fixReason, setFixReason] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [newUserId, setNewUserId] = useState("");
  const [newPlan, setNewPlan] = useState("Free");

  const loadAll = async (quiet = false) => {
    if (!quiet) setRefreshing(true);
    setLoadError(null);
    const [cl, ov, pl] = await Promise.allSettled([
      apiClient.get("/api/v1/admin/clients"),
      apiClient.get("/api/v1/admin/trading/overview"),
      apiClient.getPlans(),
    ]);
    if (cl.status === "fulfilled") {
      setClients((cl.value?.data?.clients ?? []) as ClientSub[]);
    }
    if (ov.status === "fulfilled") {
      setOverview((ov.value?.data?.users ?? []) as OverviewUser[]);
    }
    if (pl.status === "fulfilled") {
      const body: any = pl.value?.data ?? pl.value;
      setPlans(Array.isArray(body) ? body : body?.plans ?? []);
    }
    if (cl.status === "rejected" && ov.status === "rejected") {
      setLoadError("Could not load admin client data.");
    }
    setLoading(false);
    setRefreshing(false);
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") setModal(null);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  // Union of subscription rows and overview-only identities (KYC/broker
  // users without a subscription record still show up as clients).
  const rows: MergedRow[] = useMemo(() => {
    const byId = new Map<string, MergedRow>();
    for (const c of clients) byId.set(c.user_id, { ...c });
    for (const u of overview) {
      const r: MergedRow = byId.get(u.user_id) ?? { user_id: u.user_id };
      r.name = u.name ?? r.name ?? null;
      r.email = u.email ?? r.email ?? null;
      r.kyc = u.kyc_status ?? null;
      if (!r.plan_name && u.plan) r.plan_name = u.plan;
      if (!r.status && u.subscription_status) r.status = u.subscription_status;
      r.license = u.license;
      r.accounts = u.accounts;
      r.signals_30d = u.signals_30d ?? 0;
      r.signals_open = u.signals_open ?? 0;
      r.sources = u.sources;
      byId.set(u.user_id, r);
    }
    return Array.from(byId.values()).sort((a, b) =>
      (a.name || a.user_id).localeCompare(b.name || b.user_id));
  }, [clients, overview]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return rows.filter((r) => {
      if (planFilter !== "all") {
        const pn = r.plan_name || "none";
        if (pn !== planFilter) return false;
      }
      if (statusFilter !== "all") {
        const st = (r.status || "none").toLowerCase();
        if (st !== statusFilter) return false;
      }
      if (!q) return true;
      return [r.user_id, r.name, r.email, r.plan_name]
        .filter(Boolean)
        .some((f) => String(f).toLowerCase().includes(q));
    });
  }, [rows, search, planFilter, statusFilter]);

  const kpi = useMemo(() => {
    const active = rows.filter((r) => (r.status || "").toLowerCase() === "active").length;
    let accounts = 0;
    let openPos = 0;
    let stake = 0;
    let signals30 = 0;
    let signalsOpen = 0;
    for (const r of rows) {
      for (const a of r.accounts ?? []) {
        accounts += 1;
        openPos += a.open_count ?? 0;
        stake += a.open_stake_total ?? 0;
      }
      signals30 += r.signals_30d ?? 0;
      signalsOpen += r.signals_open ?? 0;
    }
    const planNames = new Set(rows.map((r) => r.plan_name).filter(Boolean) as string[]);
    const paid = rows.filter((r) => r.plan_name && r.plan_name.toLowerCase() !== "free").length;
    return { total: rows.length, active, accounts, openPos, stake, signals30, signalsOpen,
             planCount: planNames.size, paid };
  }, [rows]);

  const planOptions = useMemo(() => {
    const names = new Set<string>(plans.map((p) => p.name));
    for (const r of rows) if (r.plan_name) names.add(r.plan_name);
    names.add("Free");
    return Array.from(names).sort();
  }, [plans, rows]);

  const selectedRow = useMemo(
    () => rows.find((r) => r.user_id === selectedId) ?? null,
    [rows, selectedId]);

  const fetchDetail = async (id: string) => {
    setDetailLoading(true);
    setDetail(null);
    try {
      const res: any = await apiClient.get(`/api/v1/admin/clients/${encodeURIComponent(id)}`);
      setDetail({
        subscription: res?.data?.subscription ?? null,
        invoices: res?.data?.invoices ?? [],
        billing_history: res?.data?.billing_history ?? [],
      });
      setSetPlanName(res?.data?.subscription?.plan_id
        ? plans.find((p) => p.plan_id === res?.data?.subscription?.plan_id)?.name ?? ""
        : "");
    } catch {
      setDetail({ subscription: null, invoices: [], billing_history: [] });
    } finally {
      setDetailLoading(false);
    }
  };

  const openClient = (id: string) => {
    setSelectedId(id);
    setTab("overview");
    setActionMsg(null);
    setConfirmDelete(false);
    setModal("detail");
    fetchDetail(id);
  };

  useEffect(() => {
    if (!selectedRow) return;
    setLicTier(selectedRow.license?.tier || "standard");
    setLicEnabled(selectedRow.license?.enabled !== false);
  }, [selectedRow]);

  const runAction = async (fn: () => Promise<unknown>, okText: string) => {
    if (!selectedId) return;
    setActionBusy(true);
    setActionMsg(null);
    try {
      await fn();
      setActionMsg({ ok: true, text: okText });
      await loadAll(true);
      await fetchDetail(selectedId);
    } catch (e: any) {
      const detailMsg = e?.response?.data?.detail;
      const text = typeof detailMsg === "string"
        ? detailMsg
        : detailMsg?.message || e?.message || "Action failed";
      setActionMsg({ ok: false, text });
    } finally {
      setActionBusy(false);
    }
  };

  const onCreateClient = async () => {
    setActionBusy(true);
    setActionMsg(null);
    try {
      await apiClient.post("/api/v1/admin/clients", {
        user_id: newUserId.trim(),
        plan_name: newPlan,
      });
      setModal(null);
      setNewUserId("");
      await loadAll(true);
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      setActionMsg({ ok: false, text: typeof d === "string" ? d : e?.message || "Create failed" });
    } finally {
      setActionBusy(false);
    }
  };

  const inputCls =
    "w-full bg-neutral-950 border border-white/10 rounded px-2.5 py-2 text-xs font-mono text-white placeholder-stone-600 focus:outline-none focus:border-white/30";
  const selectCls =
    "bg-neutral-950 border border-white/10 rounded px-2.5 py-2 text-xs font-mono text-white focus:outline-none focus:border-white/30 cursor-pointer";
  const btnPrimary =
    "px-3 py-1.5 rounded bg-white text-black border border-white text-xs font-mono font-bold hover:bg-neutral-200 transition disabled:opacity-40 cursor-pointer";
  const btnGhost =
    "px-3 py-1.5 rounded border border-white/15 bg-white/5 text-white text-xs font-mono font-bold hover:bg-white/10 transition disabled:opacity-40 cursor-pointer";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal flex items-center">
            <Users className="w-7 h-7 mr-3 text-white/70" />
            Client CRM
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            Every client, plan, license and trading account in one place. Admin-only --
            actions here are audited to the client's billing history.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => loadAll()}
            disabled={refreshing}
            className={btnGhost}
            title="Refresh all data"
          >
            <RefreshCw className={`w-3.5 h-3.5 inline mr-1.5 ${refreshing ? "animate-spin" : ""}`} />
            REFRESH
          </button>
          <button
            onClick={() => {
              setActionMsg(null);
              setNewUserId("");
              setModal("new");
            }}
            className={btnPrimary}
          >
            <Plus className="w-3.5 h-3.5 inline mr-1.5" />
            NEW CLIENT
          </button>
        </div>
      </div>

      {loadError && (
        <div className="p-3 border border-rose-900/40 bg-rose-950/10 rounded-xl text-xs font-mono text-rose-300">
          {loadError}
        </div>
      )}

      {/* KPI strip (ptah TopStatsOverview pattern) */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Total clients", value: String(kpi.total),
            sub: `${kpi.active} active subscriptions` },
          { label: "Broker accounts", value: String(kpi.accounts),
            sub: `${kpi.openPos} open positions · ${fmtNum(kpi.stake)} stake` },
          { label: "Signals (30d)", value: String(kpi.signals30),
            sub: `${kpi.signalsOpen} open now` },
          { label: "Plans in use", value: String(kpi.planCount),
            sub: `${kpi.paid} paid · ${kpi.total - kpi.paid} free/none` },
        ].map((c) => (
          <div key={c.label} className="border border-white/10 rounded-xl bg-black/30 p-4">
            <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
              {c.label}
            </div>
            <div className="text-2xl font-black text-white mt-1.5 tracking-tight">{c.value}</div>
            <div className="text-[10px] font-mono text-zinc-500 mt-1">{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Search + filters (ptah PipelineBoard pattern) */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-sm flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
          <input
            type="text"
            placeholder="Search by name, email or user id..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`${inputCls} pl-9`}
          />
        </div>
        <select
          value={planFilter}
          onChange={(e) => setPlanFilter(e.target.value)}
          className={selectCls}
          title="Filter by plan"
        >
          <option value="all">All plans</option>
          {planOptions.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={selectCls}
          title="Filter by subscription status"
        >
          <option value="all">Any status</option>
          <option value="active">active</option>
          <option value="cancelled">cancelled</option>
          <option value="past_due">past_due</option>
          <option value="pending">pending</option>
          <option value="none">no subscription</option>
        </select>
        <span className="text-[10px] font-mono px-2 py-1 rounded border border-white/10 bg-white/5 text-zinc-400">
          {filtered.length}/{rows.length} clients
        </span>
      </div>

      {/* Clients master table */}
      <div className="border border-white/10 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 text-zinc-500 uppercase text-[9px] font-mono">
                <th className="py-2.5 px-3">Client</th>
                <th className="py-2.5 px-3">Plan</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Provider</th>
                <th className="py-2.5 px-3">Period end</th>
                <th className="py-2.5 px-3">License</th>
                <th className="py-2.5 px-3 text-right">Signals 30d</th>
                <th className="py-2.5 px-3 text-right">Open pos</th>
                <th className="py-2.5 px-3">Joined</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={9} className="py-10 text-center text-xs font-mono text-zinc-500">
                    <RefreshCw className="w-4 h-4 inline animate-spin text-rose-500 mr-2" />
                    LOADING CLIENTS...
                  </td>
                </tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-10 text-center text-xs font-mono text-zinc-500">
                    No clients match these filters.
                  </td>
                </tr>
              )}
              {!loading &&
                filtered.map((r) => (
                  <tr
                    key={r.user_id}
                    onClick={() => openClient(r.user_id)}
                    className="border-t border-white/5 hover:bg-white/[0.04] cursor-pointer"
                  >
                    <td className="py-2.5 px-3">
                      <div className="text-xs font-mono font-bold text-white">
                        {r.name || <span className="text-zinc-500">{r.user_id}</span>}
                      </div>
                      <div className="text-[10px] text-zinc-500 truncate max-w-[260px]">
                        {r.email || r.user_id}
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border ${planBadge(r.plan_name)}`}>
                        {r.plan_name || "none"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border ${statusBadge(r.status)}`}>
                        {r.status || "no sub"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[10px] font-mono text-zinc-400">
                      {r.payment_provider || "—"}
                    </td>
                    <td className="py-2.5 px-3 text-[10px] font-mono text-zinc-400">
                      {fmtDate(r.current_period_end)}
                    </td>
                    <td className="py-2.5 px-3 text-[10px] font-mono">
                      <span className={r.license?.enabled === false ? "text-rose-400" : "text-zinc-400"}>
                        {r.license?.tier || "standard"}
                        {r.license?.enabled === false && " (off)"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                      {r.signals_30d ?? 0}
                    </td>
                    <td className="py-2.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                      {(r.accounts ?? []).reduce((n, a) => n + (a.open_count ?? 0), 0)}
                    </td>
                    <td className="py-2.5 px-3 text-[10px] font-mono text-zinc-500">
                      {fmtDate(r.created_at)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Client detail modal (ptah LeadDetailModal pattern, simplified) */}
      {modal === "detail" && selectedRow && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
          onClick={() => setModal(null)}
        >
          <div
            className="w-full max-w-4xl max-h-[90vh] flex flex-col border border-white/10 rounded-2xl bg-zinc-950 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="px-5 py-4 border-b border-white/10 flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full border border-white/15 bg-white/5 text-zinc-400">
                    {selectedRow.user_id}
                  </span>
                  <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border ${planBadge(selectedRow.plan_name)}`}>
                    {selectedRow.plan_name || "no plan"}
                  </span>
                  <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border ${statusBadge(selectedRow.status)}`}>
                    {selectedRow.status || "no sub"}
                  </span>
                  {selectedRow.kyc && (
                    <span className="text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border border-sky-500/40 bg-sky-500/10 text-sky-300">
                      kyc: {selectedRow.kyc}
                    </span>
                  )}
                </div>
                <div className="text-white font-serif italic text-xl mt-1 truncate">
                  {selectedRow.name || selectedRow.email || selectedRow.user_id}
                </div>
                {selectedRow.email && selectedRow.name && (
                  <div className="text-[11px] text-zinc-500 font-mono">{selectedRow.email}</div>
                )}
              </div>
              <button
                onClick={() => setModal(null)}
                className="p-1.5 rounded hover:bg-white/10 transition cursor-pointer"
                title="Close (Esc)"
              >
                <X className="w-4 h-4 text-zinc-400" />
              </button>
            </div>

            {/* Tab rail */}
            <div className="px-5 pt-3 flex items-center gap-1.5 overflow-x-auto">
              {(["overview", "billing", "actions"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-3 py-1.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider transition cursor-pointer ${
                    tab === t
                      ? "bg-white text-black"
                      : "bg-white/5 text-zinc-400 hover:bg-white/10 border border-white/10"
                  }`}
                >
                  {t}
                </button>
              ))}
              {detailLoading && (
                <span className="text-[10px] font-mono text-zinc-500 animate-pulse">
                  loading billing...
                </span>
              )}
            </div>

            {actionMsg && (
              <div
                className={`mx-5 mt-3 p-2.5 rounded-lg border text-[11px] font-mono ${
                  actionMsg.ok
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                    : "border-rose-500/40 bg-rose-950/20 text-rose-300"
                }`}
              >
                {actionMsg.ok ? (
                  <CheckCircle2 className="w-3.5 h-3.5 inline mr-1.5" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 inline mr-1.5" />
                )}
                {actionMsg.text}
              </div>
            )}

            {/* Body */}
            <div className="px-5 py-4 overflow-y-auto space-y-4">
              {tab === "overview" && (
                <>
                  <div className="grid sm:grid-cols-3 gap-3">
                    {[
                      { k: "Name", v: selectedRow.name || "—" },
                      { k: "Email", v: selectedRow.email || "—" },
                      { k: "KYC status", v: selectedRow.kyc || "—" },
                      { k: "Joined", v: fmtDate(selectedRow.created_at) },
                      { k: "Signals 30d", v: String(selectedRow.signals_30d ?? 0) },
                      { k: "Open signals", v: String(selectedRow.signals_open ?? 0) },
                    ].map((f) => (
                      <div key={f.k} className="border border-white/10 rounded-lg bg-black/30 p-3">
                        <div className="text-[9px] font-mono uppercase tracking-wider text-zinc-500">
                          {f.k}
                        </div>
                        <div className="text-xs font-mono text-white mt-1 break-all">{f.v}</div>
                      </div>
                    ))}
                  </div>

                  {selectedRow.sources && selectedRow.sources.length > 0 && (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[9px] font-mono uppercase text-zinc-500 mr-1">sources:</span>
                      {selectedRow.sources.map((s) => (
                        <span
                          key={s}
                          className="text-[9px] font-mono uppercase px-2 py-0.5 rounded-full border border-white/10 bg-white/5 text-zinc-400"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Node license (PUT /admin/licenses/{id}) */}
                  <div className="border border-white/10 rounded-xl bg-black/30 p-4 space-y-3">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Node license
                    </div>
                    <div className="flex flex-wrap items-end gap-3">
                      <label className="space-y-1">
                        <span className="block text-[9px] font-mono uppercase text-zinc-500">Tier</span>
                        <select
                          value={licTier}
                          onChange={(e) => setLicTier(e.target.value)}
                          className={selectCls}
                        >
                          {["standard", "obsidian", "sovereign"].map((t) => (
                            <option key={t} value={t}>{t}</option>
                          ))}
                        </select>
                      </label>
                      <label className="flex items-center gap-2 pb-1.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={licEnabled}
                          onChange={(e) => setLicEnabled(e.target.checked)}
                          className="accent-emerald-500 cursor-pointer"
                        />
                        <span className="text-[11px] font-mono text-zinc-300">enabled</span>
                      </label>
                      <button
                        disabled={actionBusy}
                        onClick={() =>
                          runAction(
                            () =>
                              apiClient.put(
                                `/api/v1/admin/licenses/${encodeURIComponent(selectedId!)}`,
                                { tier: licTier, enabled: licEnabled }
                              ),
                            `License updated → ${licTier} (${licEnabled ? "enabled" : "disabled"})`
                          )
                        }
                        className={btnPrimary}
                      >
                        SAVE LICENSE
                      </button>
                    </div>
                  </div>

                  {/* Broker accounts (live reads via trading/overview) */}
                  <div className="space-y-2">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Broker accounts
                    </div>
                    {(selectedRow.accounts ?? []).length === 0 && (
                      <p className="text-xs font-mono text-zinc-600">No connected broker accounts.</p>
                    )}
                    {(selectedRow.accounts ?? []).map((a) => (
                      <div key={a.adapter_id} className="border border-white/10 rounded-lg bg-black/30 p-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="text-[11px] font-mono text-white">
                            {a.account_id || a.adapter_id}
                            <span className="text-zinc-600 ml-2 text-[9px]">{a.adapter_id}</span>
                          </div>
                          <div className="text-[11px] font-mono">
                            <span className="text-emerald-400 font-bold">
                              {a.balance != null ? `${fmtNum(a.balance)} ${a.currency || ""}` : "—"}
                            </span>
                            <span className="text-zinc-500 ml-3">
                              {a.open_count ?? 0} open · stake {fmtNum(a.open_stake_total)}
                            </span>
                          </div>
                        </div>
                        {(a.open_positions ?? []).length > 0 && (
                          <table className="w-full mt-2 text-left border-collapse">
                            <thead>
                              <tr className="text-zinc-600 uppercase text-[8.5px] font-mono">
                                <th className="py-1 pr-3">Symbol</th>
                                <th className="py-1 pr-3">Type</th>
                                <th className="py-1 pr-3 text-right">Stake</th>
                                <th className="py-1 text-right">Payout</th>
                              </tr>
                            </thead>
                            <tbody>
                              {(a.open_positions ?? []).map((p, i) => (
                                <tr key={p.order_id || i} className="border-t border-white/5">
                                  <td className="py-1 pr-3 text-[10px] font-mono text-white">{p.symbol || "—"}</td>
                                  <td className="py-1 pr-3 text-[10px] font-mono text-zinc-400">{p.contract_type || "—"}</td>
                                  <td className="py-1 pr-3 text-right text-[10px] font-mono text-zinc-400">{fmtNum(p.stake)}</td>
                                  <td className="py-1 text-right text-[10px] font-mono text-zinc-400">{fmtNum(p.payout)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}

              {tab === "billing" && (
                <>
                  {!detail?.subscription ? (
                    <p className="text-xs font-mono text-zinc-500">
                      No subscription record for this client.
                    </p>
                  ) : (
                    <div className="grid sm:grid-cols-3 gap-3">
                      {[
                        { k: "Plan", v: selectedRow.plan_name || detail.subscription.plan_id || "—" },
                        { k: "Status", v: detail.subscription.status || "—" },
                        { k: "Provider", v: detail.subscription.payment_provider || "—" },
                        { k: "Period start", v: fmtDate(detail.subscription.current_period_start) },
                        { k: "Period end", v: fmtDate(detail.subscription.current_period_end) },
                        { k: "Cancel at period end",
                          v: detail.subscription.cancel_at_period_end ? "yes" : "no" },
                      ].map((f) => (
                        <div key={f.k} className="border border-white/10 rounded-lg bg-black/30 p-3">
                          <div className="text-[9px] font-mono uppercase tracking-wider text-zinc-500">
                            {f.k}
                          </div>
                          <div className="text-xs font-mono text-white mt-1 break-all">{f.v}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2.5 bg-white/5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Invoices ({detail?.invoices?.length ?? 0})
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[8.5px] font-mono">
                            <th className="py-1.5 px-3">Invoice</th>
                            <th className="py-1.5 px-3 text-right">Amount</th>
                            <th className="py-1.5 px-3">Status</th>
                            <th className="py-1.5 px-3">Due</th>
                            <th className="py-1.5 px-3">Paid</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(detail?.invoices ?? []).map((inv) => (
                            <tr key={inv.invoice_id} className="border-t border-white/5">
                              <td className="py-1.5 px-3 text-[9.5px] font-mono text-zinc-500 truncate max-w-[140px]" title={inv.invoice_id}>
                                {inv.invoice_id}
                              </td>
                              <td className="py-1.5 px-3 text-right text-[10px] font-mono text-white">
                                {fmtNum(inv.amount)} {inv.currency || ""}
                              </td>
                              <td className="py-1.5 px-3">
                                <span className={`text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${statusBadge(inv.status)}`}>
                                  {inv.status || "—"}
                                </span>
                              </td>
                              <td className="py-1.5 px-3 text-[10px] font-mono text-zinc-400">{fmtDate(inv.due_date)}</td>
                              <td className="py-1.5 px-3 text-[10px] font-mono text-zinc-400">{fmtDate(inv.paid_date)}</td>
                            </tr>
                          ))}
                          {(detail?.invoices ?? []).length === 0 && (
                            <tr>
                              <td colSpan={5} className="py-5 text-center text-[10px] font-mono text-zinc-600">
                                No invoices yet.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-4 py-2.5 bg-white/5 text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Billing history ({detail?.billing_history?.length ?? 0})
                    </div>
                    <div className="max-h-48 overflow-y-auto">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="bg-white/[0.03] text-zinc-600 uppercase text-[8.5px] font-mono">
                            <th className="py-1.5 px-3">When</th>
                            <th className="py-1.5 px-3">Action</th>
                            <th className="py-1.5 px-3 text-right">Amount</th>
                            <th className="py-1.5 px-3">Status</th>
                            <th className="py-1.5 px-3">Details</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(detail?.billing_history ?? []).map((h) => (
                            <tr key={h.history_id} className="border-t border-white/5">
                              <td className="py-1.5 px-3 text-[9.5px] font-mono text-zinc-500 whitespace-nowrap">
                                {fmtDateTime(h.created_at)}
                              </td>
                              <td className="py-1.5 px-3 text-[10px] font-mono font-bold text-white">{h.action}</td>
                              <td className="py-1.5 px-3 text-right text-[10px] font-mono text-zinc-400">
                                {h.amount != null ? `${fmtNum(h.amount)} ${h.currency || ""}` : "—"}
                              </td>
                              <td className="py-1.5 px-3">
                                <span className={`text-[8.5px] font-mono uppercase px-1.5 py-0.5 rounded-full border ${statusBadge(h.status)}`}>
                                  {h.status || "—"}
                                </span>
                              </td>
                              <td
                                className="py-1.5 px-3 text-[9.5px] font-mono text-zinc-600 truncate max-w-[220px]"
                                title={h.details ? JSON.stringify(h.details) : ""}
                              >
                                {h.details ? JSON.stringify(h.details) : "—"}
                              </td>
                            </tr>
                          ))}
                          {(detail?.billing_history ?? []).length === 0 && (
                            <tr>
                              <td colSpan={5} className="py-5 text-center text-[10px] font-mono text-zinc-600">
                                No billing history yet.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}

              {tab === "actions" && (
                <div className="space-y-4">
                  {/* Set plan */}
                  <div className="border border-white/10 rounded-xl bg-black/30 p-4 space-y-3">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Set plan (upgrade / downgrade / comp)
                    </div>
                    <div className="flex flex-wrap items-end gap-3">
                      <label className="space-y-1">
                        <span className="block text-[9px] font-mono uppercase text-zinc-500">Plan</span>
                        <select
                          value={setPlanName}
                          onChange={(e) => setSetPlanName(e.target.value)}
                          className={selectCls}
                        >
                          <option value="">select plan...</option>
                          {planOptions.map((p) => (
                            <option key={p} value={p}>{p}</option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-1 flex-1 min-w-[200px]">
                        <span className="block text-[9px] font-mono uppercase text-zinc-500">Reason (audited)</span>
                        <input
                          type="text"
                          value={setPlanReason}
                          onChange={(e) => setSetPlanReason(e.target.value)}
                          placeholder="e.g. comp for outage"
                          className={inputCls}
                        />
                      </label>
                      <button
                        disabled={actionBusy || !setPlanName}
                        onClick={() =>
                          runAction(
                            () =>
                              apiClient.post(
                                `/api/v1/admin/clients/${encodeURIComponent(selectedId!)}/plan`,
                                { plan_name: setPlanName, reason: setPlanReason || null }
                              ),
                            `Plan set to ${setPlanName}`
                          ).then(() => setSetPlanReason(""))
                        }
                        className={btnPrimary}
                      >
                        APPLY PLAN
                      </button>
                    </div>
                  </div>

                  {/* Fix stuck account */}
                  <div className="border border-white/10 rounded-xl bg-black/30 p-4 space-y-3">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                      Fix stuck account
                    </div>
                    <div className="flex flex-wrap items-end gap-3">
                      <label className="space-y-1">
                        <span className="block text-[9px] font-mono uppercase text-zinc-500">Action</span>
                        <select
                          value={fixAction}
                          onChange={(e) => setFixAction(e.target.value)}
                          className={selectCls}
                        >
                          {FIX_ACTIONS.map((a) => (
                            <option key={a.id} value={a.id}>{a.label}</option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-1 flex-1 min-w-[200px]">
                        <span className="block text-[9px] font-mono uppercase text-zinc-500">Reason (audited)</span>
                        <input
                          type="text"
                          value={fixReason}
                          onChange={(e) => setFixReason(e.target.value)}
                          placeholder="e.g. support ticket #123"
                          className={inputCls}
                        />
                      </label>
                      <button
                        disabled={actionBusy}
                        onClick={() =>
                          runAction(
                            () =>
                              apiClient.post(
                                `/api/v1/admin/clients/${encodeURIComponent(selectedId!)}/fix`,
                                { action: fixAction, reason: fixReason || null }
                              ),
                            `Fix applied: ${fixAction}`
                          ).then(() => setFixReason(""))
                        }
                        className={btnGhost}
                      >
                        RUN FIX
                      </button>
                    </div>
                  </div>

                  {/* Danger zone */}
                  <div className="border border-rose-900/40 rounded-xl bg-rose-950/10 p-4 space-y-3">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold">
                      Danger zone
                    </div>
                    <p className="text-[11px] text-zinc-400 font-mono">
                      Deleting removes the subscription, invoices and billing history.
                      The Auth0 identity is untouched and they can sign up again.
                    </p>
                    <button
                      disabled={actionBusy}
                      onClick={() => {
                        if (!confirmDelete) {
                          setConfirmDelete(true);
                          return;
                        }
                        runAction(
                          () => apiClient.delete(`/api/v1/admin/clients/${encodeURIComponent(selectedId!)}`),
                          "Client record deleted"
                        ).then((r) => {
                          setConfirmDelete(false);
                          return r;
                        });
                      }}
                      className={`px-3 py-1.5 rounded text-xs font-mono font-bold border transition disabled:opacity-40 cursor-pointer ${
                        confirmDelete
                          ? "bg-rose-600 text-white border-rose-500"
                          : "bg-transparent text-rose-400 border-rose-500/40 hover:bg-rose-950/30"
                      }`}
                    >
                      {confirmDelete ? "CONFIRM DELETE (click again)" : "DELETE CLIENT"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* New client modal */}
      {modal === "new" && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
          onClick={() => setModal(null)}
        >
          <div
            className="w-full max-w-md border border-white/10 rounded-2xl bg-zinc-950 shadow-2xl p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-white font-serif italic text-xl">New client record</h2>
              <button
                onClick={() => setModal(null)}
                className="p-1.5 rounded hover:bg-white/10 transition cursor-pointer"
              >
                <X className="w-4 h-4 text-zinc-400" />
              </button>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono">
              Creates the Priv-side subscription record for an Auth0 identity (manual
              onboard / comp). The user still signs up or logs in normally.
            </p>
            {actionMsg && !actionMsg.ok && (
              <div className="p-2.5 rounded-lg border border-rose-500/40 bg-rose-950/20 text-[11px] font-mono text-rose-300">
                <AlertTriangle className="w-3.5 h-3.5 inline mr-1.5" />
                {actionMsg.text}
              </div>
            )}
            <label className="space-y-1 block">
              <span className="block text-[9px] font-mono uppercase text-zinc-500">
                Auth0 user id
              </span>
              <input
                type="text"
                value={newUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                placeholder="auth0|..."
                className={inputCls}
              />
            </label>
            <label className="space-y-1 block">
              <span className="block text-[9px] font-mono uppercase text-zinc-500">Plan</span>
              <select
                value={newPlan}
                onChange={(e) => setNewPlan(e.target.value)}
                className={selectCls}
              >
                {planOptions.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </label>
            <div className="flex justify-end gap-2">
              <button onClick={() => setModal(null)} className={btnGhost}>
                CANCEL
              </button>
              <button
                onClick={onCreateClient}
                disabled={actionBusy || !newUserId.trim()}
                className={btnPrimary}
              >
                {actionBusy ? "CREATING..." : "CREATE CLIENT"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
