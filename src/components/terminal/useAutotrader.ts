import { useCallback, useEffect, useRef, useState } from "react";

export interface AgentStatus {
  armed: boolean;
  broker_id?: string;
  platform?: string;
  symbol?: string;
  symbols?: string[] | null;
  scan_all_markets?: boolean;
  universe_size?: number | null;
  last_symbol_traded?: string | null;
  tier?: string;
  strategy?: string | null;
  strategy_params?: Record<string, unknown>;
  // What drives entries while armed: "strategy" (MAIN strategy), 
  // "own_signals" (subscriber tickets) or "global_stream" (public 6h ticket).
  signal_source?: string;
  cycles: number;
  placements: number;
  last_contract?: string | null;
  armed_at?: string | null;
  last_cycle_at?: string | null;
  logs: string[];
  // Persisted arm settings (GET /settings). Carried so the panel can show
  // the conviction gate + AI-bleed-rescue toggles against the saved value.
  settings?: {
    asset_classes?: string[];
    timeframes?: string[];
    sessions?: string[];
    weekend_only_247?: boolean;
    min_trade_score?: number;
    ai_bleed_rescue?: boolean;
  };
}

const EMPTY: AgentStatus = { armed: false, cycles: 0, placements: 0, logs: [] };

// Drives the SERVER-side autotrader (/api/autotrader/arm|disarm|status).
// The loop lives on the backend, so it keeps trading after the tab is
// closed, the user logs out or the laptop sleeps; this hook only arms,
// disarms and mirrors status. It never runs trades itself.
export function useAutotrader(
  getHeaders: () => Promise<Record<string, string>>,
  brokerId?: string | null,
) {
  const [status, setStatus] = useState<AgentStatus>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);

  const refresh = useCallback(async () => {
    try {
      // Scope status to the selected account so the dashboard swaps with
      // the demo<->real switcher (each account runs its own agent).
      const qs = brokerId ? `?broker_id=${encodeURIComponent(brokerId)}` : "";
      const res = await fetch(`/api/autotrader/status${qs}`, { headers: await getHeaders() });
      if (!res.ok) return;
      const body = await res.json();
      if (alive.current) setStatus({ ...EMPTY, ...body });
    } catch {
      /* transient: keep last known status */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brokerId]);

  useEffect(() => {
    alive.current = true;
    void refresh();
    const t = setInterval(refresh, 10000);
    return () => {
      alive.current = false;
      clearInterval(t);
    };
  }, [refresh]);

  const arm = useCallback(
    async (payload: Record<string, unknown>) => {
      setBusy(true);
      setError(null);
      try {
        const res = await fetch("/api/autotrader/arm", {
          method: "POST",
          headers: { "Content-Type": "application/json", ...(await getHeaders()) },
          body: JSON.stringify(payload),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`);
        setStatus({ ...EMPTY, ...body });
      } catch (e: any) {
        setError(e?.message || "Could not arm the agent.");
      } finally {
        setBusy(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const disarm = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const qs = brokerId ? `?broker_id=${encodeURIComponent(brokerId)}` : "";
      const res = await fetch(`/api/autotrader/disarm${qs}`, { method: "POST", headers: await getHeaders() });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`);
      setStatus({ ...EMPTY, ...body });
    } catch (e: any) {
      setError(e?.message || "Could not disarm the agent.");
    } finally {
      setBusy(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [brokerId]);

  // Persist an arm-settings patch (conviction gate / AI bleed rescue / etc.)
  // to the profile. Applies to a running agent from its next cycle -- no
  // re-arm needed. Then refreshes status so the panel reflects the saved value.
  const saveSettings = useCallback(
    async (patch: Record<string, unknown>) => {
      try {
        const res = await fetch("/api/autotrader/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...(await getHeaders()) },
          body: JSON.stringify(patch),
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`);
        await refresh();
        return true;
      } catch (e: any) {
        setError(e?.message || "Could not save settings.");
        return false;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [refresh]
  );

  return { status, busy, error, arm, disarm, refresh, saveSettings };
}
