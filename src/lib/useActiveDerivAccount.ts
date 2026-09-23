import { useEffect, useState } from "react";
import apiClient from "../api/apiClient";

export interface ActiveDerivAccount {
  loginid: string;
  account_type: "demo" | "live" | string;
  currency: string;
  broker_id: string;
  adapter_live: boolean;
}

// Resolves which Deriv account drives the given mode (demo toggle state):
// the user's per-type default, else their first account of that type,
// else null (caller falls back to simulation / shared broker).
export function useActiveDerivAccount(mode: "demo" | "live"): {
  account: ActiveDerivAccount | null;
  loading: boolean;
} {
  const [account, setAccount] = useState<ActiveDerivAccount | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient
      .getActiveDerivAccount(mode)
      .then((res: any) => {
        if (cancelled) return;
        setAccount(res?.data?.data?.account ?? res?.data?.account ?? null);
      })
      .catch(() => {
        if (!cancelled) setAccount(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode]);

  return { account, loading };
}
