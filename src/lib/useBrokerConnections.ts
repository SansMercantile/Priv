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

/**
 * Single source of truth for broker connections, including Deriv.
 *
 * Previously Deriv was a special case, read from the client-side PKCE
 * OAuth session (src/lib/derivAuth) and explicitly excluded from this
 * backend list. That flow is retired -- Deriv now connects through the
 * same backend endpoint as every other broker (see oauth_api.py), so it
 * no longer needs separate handling here.
 */
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
