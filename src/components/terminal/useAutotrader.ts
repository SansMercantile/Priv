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
  cycles: number;
  placements: number;
  last_contract?: string | null;
  armed_at?: string | null;
  last_cycle_at?: string | null;
  logs: string[];
}

const EMPTY: AgentStatus = { armed: false, cycles: 0, placements: 0, logs: [] };

// Drives the SERVER-side autotrader (/api/autotrader/arm|disarm|status).
// The loop lives on the backend, so it keeps trading after the tab is
// closed, the user logs out or the laptop sleeps; this hook only arms,
// disarms and mirrors status. It never runs trades itself.
export function useAutotrader(getHeaders: () => Promise<Record<string, string>>) {
  const [status, setStatus] = useState<AgentStatus>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/autotrader/status", { headers: await getHeaders() });
      if (!res.ok) return;
      const body = await res.json();
      if (alive.current) setStatus({ ...EMPTY, ...body });
    } catch {
      /* transient: keep last known status */
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      const res = await fetch("/api/autotrader/disarm", { method: "POST", headers: await getHeaders() });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`);
      setStatus({ ...EMPTY, ...body });
    } catch (e: any) {
      setError(e?.message || "Could not disarm the agent.");
    } finally {
      setBusy(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { status, busy, error, arm, disarm, refresh };
}
