import { useCallback, useEffect, useState } from "react";
import apiClient from "../api/apiClient";

export interface BrokerConnection {
  broker: string;
  account_type: "demo" | "live" | "paper" | string;
  status: string;
  connected_at?: string;
}

export interface BrokerConnectionsState {
  connections: BrokerConnection[];
  hasRealDeriv: boolean;
  hasDemoDeriv: boolean;
  loading: boolean;
  refresh: () => void;
}

/** Single source of truth for "does this user actually have a real/demo
 * Deriv account connected", backed by the real backend record rather than
 * any localStorage flag. Used to gate the demo/real toggle and the
 * "Live Dashboard Locked" screen consistently. */
export function useBrokerConnections(): BrokerConnectionsState {
  const [connections, setConnections] = useState<BrokerConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient
      .getBrokerConnections()
      .then(({ data }) => {
        if (cancelled) return;
        setConnections(data?.data?.connections || []);
      })
      .catch(() => {
        if (!cancelled) setConnections([]);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const derivConns = connections.filter((c) => c.broker === "deriv");
  const hasRealDeriv = derivConns.some((c) => c.account_type === "live");
  const hasDemoDeriv = derivConns.some((c) => c.account_type === "demo");

  return { connections, hasRealDeriv, hasDemoDeriv, loading, refresh };
}
