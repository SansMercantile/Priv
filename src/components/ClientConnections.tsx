import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Brain, Landmark, Link2, Gift, Copy, CheckCircle2, ExternalLink } from "lucide-react";
import apiClient from "../api/apiClient";
import DerivConnectCard from "./DerivConnectCard";
import TradingViewCard from "./TradingViewCard";
import MT5BridgeCard from "./MT5BridgeCard";

// Ordinary-user view of SANS Network Link: ONLY what applies to a client --
// the AI Core entry point, their OWN country's eTax portal (never a picker
// of random countries), real brokers (Deriv OAuth + XM/IFX/FBS affiliate
// links from the backend directory), and their referral code. Cluster
// topology, gateway simulators, sandbox theater, and hardcoded exchange
// balances stay on the admin/autonomous view in Connections.tsx.

interface BrokerEntry {
  id: string;
  name: string;
  kind: string;
  url?: string;
  login_path?: string;
  description?: string;
  affiliate?: boolean;
  has_api?: boolean;
}

function useMyTaxCountry() {
  const [mine, setMine] = useState<any>(null);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.getMyTaxCountry();
        if (!cancelled) setMine(res?.data?.data ?? res?.data ?? null);
      } catch {
        /* unauthenticated: prompt for KYC below */
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return { mine, loaded };
}

function useSignalBrokers() {
  const [brokers, setBrokers] = useState<BrokerEntry[]>([]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.getSignalBrokers();
        const d = res?.data?.data ?? res?.data ?? {};
        if (!cancelled) setBrokers(d.brokers || []);
      } catch {
        /* offline: Deriv card still renders */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  return brokers;
}

function useReferral() {
  const [ref, setRef] = useState<{ code?: string; link?: string; referred_count?: number } | null>(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.getMyReferral();
        if (!cancelled) setRef(res?.data ?? res ?? null);
      } catch {
        /* unauthenticated */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);
  const copy = async () => {
    if (!ref?.link) return;
    try {
      await navigator.clipboard.writeText(ref.link);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  };
  return { ref, copied, copy };
}

export default function ClientConnections() {
  const { mine, loaded } = useMyTaxCountry();
  const brokers = useSignalBrokers();
  const { ref, copied, copy } = useReferral();
  const affiliates = brokers.filter((b) => b.id !== "deriv");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-serif italic text-white flex items-center">
          <Link2 className="w-8 h-8 mr-3 text-white/75" />
          SANS Network Link
        </h1>
        <p className="text-white/40 text-xs mt-1 font-light">Your AI core, tax portal, brokers, and referrals.</p>
      </div>

      {/* 1. Sovereign Cognitive Hub */}
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
        <h2 className="text-base font-serif italic text-white mb-2 flex items-center">
          <Brain className="w-4 h-4 mr-2 text-white/80" />
          Sovereign Cognitive Hub (AI Core)
        </h2>
        <p className="text-xs text-zinc-400 mb-4">
          Your sovereign AI engine for market analysis and autonomous execution.
        </p>
        <Link
          to="/dashboard/agi-core"
          className="inline-block px-4 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-zinc-200 transition"
        >
          Open AI Core
        </Link>
      </div>

      {/* 2. Own-country eTax portal only */}
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
        <h2 className="text-base font-serif italic text-white mb-2 flex items-center">
          <Landmark className="w-4 h-4 mr-2 text-[#FF6B35]" />
          Sovereign Asset &amp; eTax Integration Portal
        </h2>
        {!loaded ? (
          <p className="text-xs text-zinc-500 font-mono">Loading…</p>
        ) : mine?.country ? (
          <>
            <p className="text-xs text-zinc-300 font-mono">
              {mine.name} ({mine.country}) — {mine.tax_authority}
            </p>
            <p className="text-[11px] text-zinc-500 font-mono mt-1">
              Matched from your {mine.source === "tax_residency" ? "KYC tax residency" : mine.source === "address" ? "KYC address" : "country of residence"}.
            </p>
            <Link
              to="/dashboard/profile?tab=tax"
              className="inline-block mt-3 px-4 py-2 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition"
            >
              Open eTax Portal
            </Link>
          </>
        ) : (
          <>
            <p className="text-xs text-zinc-400">
              Complete verification so we can open the eTax portal for your country.
            </p>
            <Link
              to="/dashboard/profile"
              className="inline-block mt-3 px-4 py-2 bg-white text-black rounded-lg font-mono text-xs hover:bg-zinc-200 transition"
            >
              Complete Profile &amp; KYC
            </Link>
          </>
        )}
      </div>

      {/* 3. Real brokers */}
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5 space-y-4">
        <h2 className="text-base font-serif italic text-white flex items-center">
          <Link2 className="w-4 h-4 mr-2 text-white/80" />
          Broker Connections
        </h2>
        <DerivConnectCard />
        <TradingViewCard />
        <MT5BridgeCard />
        {affiliates.map((b) => (
          <div
            key={b.id}
            className="flex items-center justify-between gap-3 p-3 rounded-lg border border-white/10 bg-black/40"
          >
            <div className="min-w-0">
              <div className="text-sm text-white font-semibold">{b.name}</div>
              {b.description && (
                <div className="text-[11px] text-zinc-500 font-mono mt-0.5">{b.description}</div>
              )}
            </div>
            {b.url && (
              <a
                href={b.url}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition"
              >
                Open account <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        ))}
      </div>

      {/* 4. Referrals */}
      <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
        <h2 className="text-base font-serif italic text-white mb-2 flex items-center">
          <Gift className="w-4 h-4 mr-2 text-white/80" />
          Referrals
        </h2>
        {ref?.code ? (
          <>
            <p className="text-xs text-zinc-400">
              Share your link — every account that registers with it binds to you permanently.
            </p>
            <div className="mt-2 flex items-center gap-2">
              <code className="flex-1 truncate px-3 py-2 bg-black border border-white/10 rounded-lg text-xs text-white font-mono">
                {ref.link}
              </code>
              <button
                onClick={copy}
                className="shrink-0 px-3 py-2 border border-white/20 rounded-lg font-mono text-xs text-white hover:bg-white/10 transition flex items-center gap-1.5"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono mt-2">
              Code <span className="text-white">{ref.code}</span> · {ref.referred_count ?? 0} referred
            </p>
          </>
        ) : (
          <p className="text-xs text-zinc-500 font-mono">Sign in to get your referral link.</p>
        )}
      </div>
    </div>
  );
}
