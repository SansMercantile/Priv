import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { toast } from '../components/ui/use-toast';
import { readDemoMode, writeDemoMode } from '../lib/environment';

interface EnvironmentContextValue {
  demoMode: boolean;
  setDemoMode: (enabled: boolean) => void;
  toggleDemoMode: () => void;
}

const EnvironmentContext = createContext<EnvironmentContextValue | null>(null);

export function EnvironmentProvider({ children }: { children: React.ReactNode }) {
  const [demoMode, setDemoModeState] = useState<boolean>(() => readDemoMode());

  const setDemoMode = useCallback((enabled: boolean) => {
    setDemoModeState(enabled);
    writeDemoMode(enabled);
    toast({
      title: enabled ? '🚀 Demo Environment Activated' : '🛡️ Live Environment Activated',
      description: enabled
        ? 'You are now in a simulated environment. Sample portfolios, news, and broker data are shown. No real account or KYC is required to explore.'
        : 'Welcome to the real Priv environment. To unlock full analysis and trading, please create your account, complete the KYC verification, and link your broker.',
      duration: 10000,
    });
  }, []);

  const toggleDemoMode = useCallback(() => {
    setDemoMode(!demoMode);
  }, [demoMode, setDemoMode]);

  useEffect(() => {
    writeDemoMode(demoMode);
  }, [demoMode]);

  const value = useMemo(
    () => ({ demoMode, setDemoMode, toggleDemoMode }),
    [demoMode, setDemoMode, toggleDemoMode]
  );

  return (
    <EnvironmentContext.Provider value={value}>{children}</EnvironmentContext.Provider>
  );
}

export function useEnvironment(): EnvironmentContextValue {
  const ctx = useContext(EnvironmentContext);
  if (!ctx) {
    throw new Error('useEnvironment must be used within EnvironmentProvider');
  }
  return ctx;
}
