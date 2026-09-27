import { useCallback, useEffect, useState } from "react";
import apiClient from "../api/apiClient";

export interface BrokerConnection {
  broker: string;
  account_type: "demo" | "live" | "paper" | string;
  status: string;
  connected_at?: string;
  loginid?: string;
  currency?: string;
  accounts?: Array<{ account_id: string; currency: string }>;
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
    let retryTimer: number | undefined;
    setLoading(true);

    apiClient
      .getBrokerConnections()
      .then(({ data }) => {
        if (cancelled) return;
        const list = data?.data?.connections || [];
        setConnections(list);
        // Empty on first load often means a race, not absence: the
        // Auth0 token may not have been renewable yet, or the claim
        // landed a beat later (the locked screen + "no linked account"
        // with a populated card is exactly this). One delayed retry.
        if (list.length === 0) {
          retryTimer = window.setTimeout(() => {
            if (cancelled) return;
            apiClient
              .getBrokerConnections()
              .then(({ data: d2 }) => {
                if (cancelled) return;
                const l2 = d2?.data?.connections || [];
                if (l2.length > 0) setConnections(l2);
              })
              .catch(() => {
                /* keep previous state */
              });
          }, 3000);
        }
      })
      .catch(() => {
        if (!cancelled) setConnections([]);
      })
      .finally(() => !cancelled && setLoading(false));

    // Any instance linking an account (DerivConnectCard) broadcasts
    // priv:deriv-linked -- every hook instance re-fetches so gates and
    // status text converge without a page reload.
    const onLinked = () => {
      if (!cancelled) refresh();
    };
    window.addEventListener("priv:deriv-linked", onLinked);

    return () => {
      cancelled = true;
      if (retryTimer) window.clearTimeout(retryTimer);
      window.removeEventListener("priv:deriv-linked", onLinked);
    };
  }, [tick, refresh]);

  const derivConns = connections.filter((c) => c.broker === "deriv");
  const hasRealDeriv = derivConns.some((c) => c.account_type === "live");
  const hasDemoDeriv = derivConns.some((c) => c.account_type === "demo");

  return { connections, hasRealDeriv, hasDemoDeriv, loading, refresh };
}
