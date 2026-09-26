import React, { useEffect, useState } from "react";
import { Radio, RefreshCw, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/apiClient";

// "My Signals" tab: the subscriber signal product, real data only.
// - Today's ticket (GET /api/signals/current, stale-flagged archive when live budgets out)
// - Instrument preferences per tier (GET/POST /api/v1/signals/preferences + /categories + /tiers)
// - Personal + global history (GET /api/v1/signals/history)
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
  const [limits, setLimits] = useState<TierLimits | null>(null);
  const [categories, setCategories] = useState<Record<string, { label: string; instruments: Record<string, string> }>>({});
  const [channels, setChannels] = useState<string[]>(["email"]);
  const [current, setCurrent] = useState<any>(null);
  const [mine, setMine] = useState<any[]>([]);
  const [global, setGlobal] = useState<any[]>([]);

  // Preference form state
  const [cat, setCat] = useState("synthetics");
  const [picked, setPicked] = useState<string[]>([]);
  const [channel, setChannel] = useState("email");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [saveErr, setSaveErr] = useState<string | null>(null);

  // OTP verification state: which contacts are proven-owned. Delivery
  // is gated server-side on this -- unverified contacts are stored but
  // never delivered to (the engine holds the signal and says why).
  const [verified, setVerified] = useState<{ channel: string; contact: string }[]>([]);
  const [otpContact, setOtpContact] = useState<"email" | "phone">("email");
  const [otpCode, setOtpCode] = useState("");
  const [otpBusy, setOtpBusy] = useState(false);
  const [otpMsg, setOtpMsg] = useState<string | null>(null);
  const [otpErr, setOtpErr] = useState<string | null>(null);

  // Same normalization as the backend (_normalize_contact): email
  // lowercased, phones stripped of visual separators.
  const normContact = (ch: string, s: string) => {
    const t = s.trim();
    return ch === "email" ? t.toLowerCase() : t.replace(/[\s\-().]/g, "");
  };
  const isVerified = (ch: string, contact: string) =>
    !!contact.trim() &&
    verified.some((v) => v.channel === ch && normContact(ch, v.contact) === normContact(ch, contact));

  const load = async () => {
    setLoading(true);
    setError(null);
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
          setEmail(p.contact_email || "");
          setPhone(p.contact_phone || "");
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
    } catch (e: any) {
      setError(e?.message || "Could not load signals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
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
        contact_email: email.trim() || undefined,
        contact_phone: phone.trim() || undefined,
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

  const sendCode = async () => {
    const contact = otpContact === "email" ? email.trim() : phone.trim();
    const ch = otpContact === "email" ? "email" : channel === "whatsapp" ? "whatsapp" : "sms";
    if (!contact) {
      setOtpErr("Enter the address/number first.");
      return;
    }
    setOtpBusy(true);
    setOtpMsg(null);
    setOtpErr(null);
    try {
      await apiClient.requestOtp(ch, contact);
      setOtpMsg(`Code sent via ${ch} — expires in 10 minutes.`);
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setOtpErr(typeof detail === "string" ? detail : detail?.message || e?.message || "Could not send code.");
    } finally {
      setOtpBusy(false);
    }
  };

  const confirmCode = async () => {
    const contact = otpContact === "email" ? email.trim() : phone.trim();
    const ch = otpContact === "email" ? "email" : channel === "whatsapp" ? "whatsapp" : "sms";
    if (!otpCode.trim()) {
      setOtpErr("Enter the 6-digit code.");
      return;
    }
    setOtpBusy(true);
    setOtpMsg(null);
    setOtpErr(null);
    try {
      const res: any = await apiClient.confirmOtp(ch, contact, otpCode.trim());
      const d = res?.data?.data ?? res?.data ?? {};
      setVerified(d.verified || []);
      setOtpCode("");
      setOtpMsg("Verified. Signals will now deliver to this contact.");
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      setOtpErr(typeof detail === "string" ? detail : detail?.message || e?.message || "Verification failed.");
    } finally {
      setOtpBusy(false);
    }
  };

  const VerifyBadge = ({ ch, contact }: { ch: string; contact: string }) => {
    if (!contact.trim()) return null;
    const ok = isVerified(ch, contact);
    return (
      <span className={`ml-2 text-[9px] uppercase px-1.5 py-0.5 rounded font-mono ${ok ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
        {ok ? "verified" : "unverified — no delivery"}
      </span>
    );
  };

  const SignalRow = ({ s }: { s: any }) => (
    <div className="flex items-center justify-between gap-2 p-2 rounded-lg border border-white/10 bg-black/40 text-xs font-mono">
      <div className="min-w-0">
        <span className="text-white font-bold truncate">{s.display_name || s.symbol}</span>{" "}
        <span className={`text-[9px] uppercase px-1.5 py-0.5 rounded ${s.direction === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"}`}>
          {s.direction}
        </span>{" "}
        {s.status && <span className="text-zinc-500 text-[10px]">{s.status}</span>}
      </div>
      <div className="text-right text-[10px] text-zinc-400 whitespace-nowrap">
        <div>IN {s.entry}</div>
        <div className="text-emerald-400">TP {s.take_profit_1}</div>
        <div className="text-rose-400">SL {s.stop_loss}</div>
      </div>
    </div>
  );

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
          <div>
            <label className="text-[11px] font-mono text-zinc-400 uppercase">Contact email{channel === "email" ? " *" : ""}<VerifyBadge ch="email" contact={email} /></label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1 w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
          <div>
            <label className="text-[11px] font-mono text-zinc-400 uppercase">Phone{(channel === "sms" || channel === "whatsapp") ? " *" : ""}<VerifyBadge ch={channel === "whatsapp" ? "whatsapp" : "sms"} contact={phone} /></label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+27…"
              className="mt-1 w-full bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
        </div>
        <div className="rounded-lg border border-white/10 bg-black/30 p-3 space-y-2">
          <p className="text-[11px] font-mono text-zinc-300">
            Verify ownership to receive signals — unverified contacts are stored but never delivered to.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={otpContact}
              onChange={(e) => setOtpContact(e.target.value as "email" | "phone")}
              className="bg-black border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white font-mono"
            >
              <option value="email">email</option>
              <option value="phone">phone (sms{channel === "whatsapp" ? "/whatsapp" : ""})</option>
            </select>
            <button
              type="button"
              onClick={sendCode}
              disabled={otpBusy}
              className="px-3 py-1.5 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition disabled:opacity-50"
            >
              {otpBusy ? "SENDING…" : "SEND CODE"}
            </button>
            <input
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="6-digit code"
              inputMode="numeric"
              className="w-28 bg-black border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white font-mono"
            />
            <button
              type="button"
              onClick={confirmCode}
              disabled={otpBusy}
              className="px-3 py-1.5 bg-white text-black rounded-lg font-mono text-xs hover:bg-zinc-200 transition disabled:opacity-50"
            >
              VERIFY
            </button>
          </div>
          {otpMsg && <p className="text-[11px] font-mono text-emerald-300">{otpMsg}</p>}
          {otpErr && <p className="text-[11px] font-mono text-red-300">{otpErr}</p>}
        </div>
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
            <SignalRow key={s.id || `${s.symbol}-${s.created_at}`} s={s} />
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
