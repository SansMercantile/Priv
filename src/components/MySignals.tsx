import React, { useEffect, useState } from "react";
import { Radio, RefreshCw, AlertTriangle, CheckCircle2, BellRing } from "lucide-react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/apiClient";
import { getAuthToken } from "../lib/authToken";

// "My Signals" tab: the subscriber signal product, real data only.
// - Today's ticket (GET /api/signals/current, stale-flagged archive when live budgets out)
// - Instrument preferences per tier (GET/POST /api/v1/signals/preferences + /categories + /tiers)
// - Personal + global history (GET /api/v1/signals/history)
// - In-app notification feed (GET /api/v1/signals/notifications + /read):
//   unread badge + banner on arrival, new rows highlighted, auto-read ack.
// Tier gates (category allow-list, max instruments, Sovereign-only events,
// contact required per channel) are enforced server-side; backend 4xx text
// is shown inline so the user knows exactly what their tier allows.

interface TierLimits {
  daily_signals: number;
  categories: string[];
  max_instruments: number;
  events: boolean;
}

interface Prefs {
  category: string;
  instruments: string[];
  delivery_channel: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  broker?: string;
}

export default function MySignals() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tier, setTier] = useState<string>("free");
  const [authState, setAuthState] = useState<boolean | null>(null);
  const [limits, setLimits] = useState<TierLimits | null>(null);
  const [categories, setCategories] = useState<Record<string, { label: string; instruments: Record<string, string> }>>({});
  const [channels, setChannels] = useState<string[]>(["email"]);
  const [current, setCurrent] = useState<any>(null);
  const [mine, setMine] = useState<any[]>([]);
  const [global, setGlobal] = useState<any[]>([]);
  // In-app notification state: unread = signals issued since the last
  // feed open (backend marker); lastSeen also drives row highlighting.
  const [unread, setUnread] = useState(0);
  const [lastSeen, setLastSeen] = useState<string | null>(null);

  const loadNotifications = async (ackRead: boolean) => {
    try {
      const res: any = await apiClient.getSignalNotifications(50);
      const d = res?.data?.data ?? res?.data ?? {};
      const n = d.unread || 0;
      setUnread(n);
      setLastSeen(typeof d.last_seen === "string" ? d.last_seen : null);
      if (ackRead && n > 0) {
        // Ack after the banner has had time to render; keeps the sidebar
        // badge and this banner in sync on the next poll.
        window.setTimeout(() => {
          apiClient.markSignalNotificationsRead().catch(() => {});
        }, 2500);
      }
    } catch {
      /* feed unreachable: no badge, no ack -- never block the page */
    }
  };

  // Preference form state
  const [cat, setCat] = useState("synthetics");
  const [picked, setPicked] = useState<string[]>([]);
  const [channel, setChannel] = useState("email");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  // Delivery is gated server-side on Profile-verified contacts only --
  // this tab no longer collects or verifies email/phone itself (see
  // UserProfileEditor.tsx / ContactVerifier.tsx). We just read what's
  // already verified so the person knows where signals will go.
  const [verified, setVerified] = useState<{ channel: string; contact: string }[]>([]);
  const verifiedEmail = verified.find((v) => v.channel === "email")?.contact || "";
  const verifiedPhone = verified.find((v) => v.channel === "sms" || v.channel === "whatsapp")?.contact || "";

  const load = async () => {
    setLoading(true);
    setError(null);
    // Whether the backend can see a signed-in identity on this call.
    // Without it every tier/preference read resolves anonymously (free
    // limits) no matter what plan the account holds.
    getAuthToken().then(
      (t) => setAuthState(!!t),
      () => setAuthState(false)
    );
    try {
      const [tiersRes, catsRes, prefsRes, histRes, curRes, verRes] = await Promise.allSettled([
        apiClient.getSignalTiers(),
        apiClient.getSignalCategories(),
        apiClient.getSignalPreferences(),
        apiClient.getSignalHistory(50),
        apiClient.getCurrentSignal(),
        apiClient.getVerifiedContacts(),
      ]);
      if (tiersRes.status === "fulfilled") {
        const d = tiersRes.value?.data?.data ?? tiersRes.value?.data ?? {};
        setTier(d.mine || "free");
        setLimits(d.limits || null);
      }
      if (catsRes.status === "fulfilled") {
        const d = catsRes.value?.data?.data ?? catsRes.value?.data ?? {};
        setCategories(d.categories || {});
        setChannels(d.channels || ["email"]);
      }
      if (prefsRes.status === "fulfilled") {
        const p: Prefs | null =
          prefsRes.value?.data?.data?.preferences ?? prefsRes.value?.data?.preferences ?? null;
        if (p) {
          setCat(p.category || "synthetics");
          setPicked(p.instruments || []);
          setChannel(p.delivery_channel || "email");
        }
      }
      if (histRes.status === "fulfilled") {
        const d = histRes.value?.data?.data ?? histRes.value?.data ?? {};
        setMine(d.mine || []);
        setGlobal(d.global || []);
      }
      if (curRes.status === "fulfilled") {
        setCurrent(curRes.value?.data?.data ?? curRes.value?.data ?? null);
      }
      if (verRes.status === "fulfilled") {
        const d = verRes.value?.data?.data ?? verRes.value?.data ?? {};
        setVerified(d.verified || []);
      }
      await loadNotifications(true);
    } catch (e: any) {
      setError(e?.message || "Could not load signals.");
    } finally {
      setLoading(false);
    }
  };

  // Light refresh for the polling tick: signal lists + current ticket +
  // unread count, without re-fetching tiers/categories/prefs.
  const refreshFeed = async () => {
    const [histRes, curRes] = await Promise.allSettled([
      apiClient.getSignalHistory(50),
      apiClient.getCurrentSignal(),
    ]);
    if (histRes.status === "fulfilled") {
      const d = histRes.value?.data?.data ?? histRes.value?.data ?? {};
      setMine(d.mine || []);
      setGlobal(d.global || []);
    }
    if (curRes.status === "fulfilled") {
      setCurrent(curRes.value?.data?.data ?? curRes.value?.data ?? null);
    }
    await loadNotifications(true);
  };

  useEffect(() => {
    load();
    // Signals rotate every 15 minutes server-side: keep the lists, the
    // current ticket and the unread badge live while the tab is open.
    const interval = window.setInterval(() => {
      refreshFeed();
    }, 60000);
    const onVisible = () => {
      if (!document.hidden) refreshFeed();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  // When the category changes, keep only instruments that exist in it.
  useEffect(() => {
    const allowed = new Set(Object.keys(categories[cat]?.instruments || {}));
    setPicked((prev) => prev.filter((i) => allowed.has(i)));
  }, [cat, categories]);

  const toggleInstrument = (code: string) => {
    setPicked((prev) => {
      if (prev.includes(code)) return prev.filter((i) => i !== code);
      const max = limits?.max_instruments ?? 3;
      if (prev.length >= max) return prev;
      return [...prev, code];
    });
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveMsg(null);
    setSaveErr(null);
    try {
      const res: any = await apiClient.setSignalPreferences({
        category: cat,
        instruments: picked,
        delivery_channel: channel,
        broker: "deriv",
      });
      const p: Prefs | null = res?.data?.data?.preferences ?? res?.data?.preferences ?? null;
      if (p) {
        setPicked(p.instruments || []);
        setChannel(p.delivery_channel || channel);
      }
      setSaveMsg("Preferences saved. Signals will follow your tier limits.");
    } catch (err: any) {
      // Backend tier/validation detail (e.g. "Category 'events' is not in
      // your tier", "At most 3 instruments on your tier") surfaces here.
      const detail = err?.response?.data?.detail;
      setSaveErr(
        typeof detail === "string" ? detail : detail?.message || err?.message || "Could not save preferences."
      );
    } finally {
      setSaving(false);
    }
  };

  const instrEntries = Object.entries(categories[cat]?.instruments || {});
  const maxInstr = limits?.max_instruments ?? 3;
  const allowedCats = limits?.categories ?? ["synthetics"];

  const ContactBadge = ({ label, contact }: { label: string; contact: string }) => (
    <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-mono ${contact ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
      {contact ? `${label}: ${contact}` : `${label}: not verified`}
    </span>
  );

  const SignalRow = ({ s, isNew }: { s: any; isNew?: boolean }) => (
    <div className={`flex items-center justify-between gap-2 p-2 rounded-lg border text-xs font-mono ${
      isNew ? "border-rose-500/40 bg-rose-500/5" : "border-white/10 bg-black/40"}`}>
      <div className="min-w-0">
        <span className="text-white font-bold truncate">{s.display_name || s.symbol}</span>{" "}
        <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${s.direction === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
          {s.direction}
        </span>{" "}
        {s.status && <span className="text-zinc-500 text-[10px]">{s.status}</span>}
        {isNew && (
          <span className="ml-1.5 text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#e11d48]/20 text-rose-300">new</span>
        )}
      </div>
      <div className="text-right text-[10px] text-zinc-400 whitespace-nowrap">
        <div>IN {s.entry}</div>
        <div className="text-emerald-400">TP {s.take_profit_1}</div>
        <div className="text-rose-400">SL {s.stop_loss}</div>
      </div>
    </div>
  );

  // A signal counts as "new" until the feed's read marker passes it.
  // Never opened the feed (no marker) -> everything is new.
  const isNewSignal = (s: any) =>
    Boolean(s?.created_at) && (!lastSeen || String(s.created_at) > lastSeen);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <Radio className="w-8 h-8 mr-3 text-white/75" />
            My Signals
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            Tier <span className="text-white font-mono uppercase">{tier}</span>
            {limits && (
              <> · {limits.daily_signals}/day · up to {limits.max_instruments} instruments</>
            )}
            {authState === false && (
              <> · <span className="text-amber-400 font-mono">not signed in — limits reflect the logged-out tier; sign in for your plan</span></>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate("/dashboard/billing")}
            className="px-3.5 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-zinc-200 transition"
          >
            UPGRADE
          </button>
          <button
            onClick={load}
            className="flex items-center space-x-2 px-3.5 py-2 hover:bg-white/10 text-white border border-white/10 rounded-lg font-mono text-xs transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{error}</div>
      )}

      {unread > 0 && (
        <div className="p-3 rounded border border-rose-500/20 bg-rose-500/5 text-rose-300 text-xs font-mono flex items-center gap-2">
          <BellRing className="w-4 h-4 shrink-0" />
          {unread} new signal{unread === 1 ? "" : "s"} since your last visit
          {mine.some((s) => isNewSignal(s)) && " — highlighted below"}
        </div>
      )}

      {/* Today's ticket */}
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
        <h2 className="text-sm font-semibold text-white mb-2">Today&apos;s signal</h2>
        {current ? (
          <>
            <SignalRow s={current} />
            {current.stale && (
              <p className="text-[10px] text-amber-400/80 font-mono mt-2">
                Archived ticket (live engine budget elapsed) — shown as-is, not regenerated.
              </p>
            )}
          </>
        ) : (
          <p className="text-xs text-zinc-500 font-mono">{loading ? "Loading…" : "No signal right now."}</p>
        )}
      </div>

      {/* Instrument preferences */}
      <form onSubmit={save} className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-4">
        <h2 className="text-sm font-semibold text-white">Signal instruments &amp; delivery</h2>
        <div>
          <label className="text-[11px] font-mono text-zinc-400 uppercase">Market category</label>
          <select
            value={cat}
            onChange={(e) => setCat(e.target.value)}
            className="mt-1 w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
          >
            {Object.entries(categories).map(([key, c]) => (
              <option key={key} value={key} disabled={!allowedCats.includes(key)}>
                {c.label}{allowedCats.includes(key) ? "" : " (not in your tier)"}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-[11px] font-mono text-zinc-400 uppercase">
            Instruments ({picked.length}/{maxInstr} on your tier)
          </label>
          <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {instrEntries.map(([code, label]) => (
              <label key={code} className="flex items-center gap-2 text-xs font-mono text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={picked.includes(code)}
                  onChange={() => toggleInstrument(code)}
                  className="accent-white"
                />
                <span className="text-white">{code}</span>
                <span className="text-zinc-500 truncate">{label}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-mono text-zinc-400 uppercase">Channel</label>
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="mt-1 w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            >
              {channels.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="text-[11px] font-mono text-zinc-400 uppercase">Delivery contact</label>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <ContactBadge label="Email" contact={verifiedEmail} />
              <ContactBadge label="Phone" contact={verifiedPhone} />
              <button
                type="button"
                onClick={() => navigate("/dashboard/profile")}
                className="text-[10px] font-mono text-white/60 hover:text-white underline underline-offset-2"
              >
                verify or change in Profile →
              </button>
            </div>
          </div>
        </div>
        <p className="text-[10px] font-mono text-zinc-500">
          Signals deliver only to email/phone verified once in your Profile — not here. Unverified contacts hold the signal instead of sending it.
        </p>
        {saveMsg && (
          <div className="p-2 rounded border border-emerald-500/20 bg-emerald-500/5 text-emerald-300 text-xs font-mono flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {saveMsg}
          </div>
        )}
        {saveErr && (
          <div className="p-2 rounded border border-red-500/20 bg-red-500/5 text-red-300 text-xs font-mono flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> {saveErr}
          </div>
        )}
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-zinc-200 transition disabled:opacity-50"
        >
          {saving ? "SAVING…" : "SAVE PREFERENCES"}
        </button>
      </form>

      {/* History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-1.5">
          <h2 className="text-sm font-semibold text-white mb-2">My issued signals</h2>
          {mine.length === 0 && <p className="text-xs text-zinc-500 font-mono">None issued to you yet.</p>}
          {mine.map((s: any) => (
            <SignalRow key={s.id || `${s.symbol}-${s.created_at}`} s={s} isNew={isNewSignal(s)} />
          ))}
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-1.5">
          <h2 className="text-sm font-semibold text-white mb-2">Global archive</h2>
          {global.length === 0 && <p className="text-xs text-zinc-500 font-mono">Archive empty.</p>}
          {global.slice(0, 20).map((s: any) => (
            <SignalRow key={s.id || `${s.symbol}-${s.created_at}`} s={s} />
          ))}
        </div>
      </div>
    </div>
  );
}
