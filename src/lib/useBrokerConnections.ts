import { useCallback, useEffect, useState } from "react";
import apiClient from "../api/apiClient";
import { getDerivAccounts } from "./derivAuth";

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
 * Deriv account connected". Deriv itself is checked via the real
 * client-side PKCE OAuth session (src/lib/derivAuth) - that's the account
 * data Deriv's own API returned, not a localStorage flag we invented.
 * Other brokers (Alpaca, etc.) still go through the backend connections
 * endpoint. */
export function useBrokerConnections(): BrokerConnectionsState {
  const [connections, setConnections] = useState<BrokerConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    // Deriv: real account data from the client-side OAuth session.
    const derivAccounts = getDerivAccounts() || [];
    const derivConns: BrokerConnection[] = derivAccounts.map((a) => ({
      broker: "deriv",
      account_type: a.account_type === "demo" ? "demo" : "live",
      status: "connected",
    }));

    // Other brokers (Alpaca, etc.): still via the backend.
    apiClient
      .getBrokerConnections()
      .then(({ data }) => {
        if (cancelled) return;
        const backendConns: BrokerConnection[] = (data?.data?.connections || []).filter(
          (c: BrokerConnection) => c.broker !== "deriv" // Deriv comes from derivAuth now
        );
        setConnections([...derivConns, ...backendConns]);
      })
      .catch(() => {
        if (!cancelled) setConnections(derivConns);
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
