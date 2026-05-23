import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { toast } from '../components/ui/use-toast';
import { readDemoMode, writeDemoMode } from '../lib/environment';

interface EnvironmentContextValue {
  demoMode: boolean;
  setDemoMode: (enabled: boolean) => void;
  toggleDemoMode: () => void;
}

const EnvironmentContext = createContext<EnvironmentContextValue | null>(null);

function shouldForceDemoPreview(): boolean {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location.search).get('preview') === 'broker';
}

export function EnvironmentProvider({ children }: { children: React.ReactNode }) {
  const [demoMode, setDemoModeState] = useState<boolean>(() => shouldForceDemoPreview() || readDemoMode());
  const previewMode = shouldForceDemoPreview();

  const setDemoMode = useCallback((enabled: boolean) => {
    setDemoModeState(enabled);
    if (!previewMode) {
      writeDemoMode(enabled);
    }
    toast({
      title: enabled ? 'Demo environment activated' : 'Live environment activated',
      description: enabled
        ? 'Sample portfolios, news, and broker data are shown. No real account or KYC is required.'
        : 'Connect your Priv account, complete KYC, customize your profile, and link a broker to unlock analysis.',
      duration: 8000,
    });
  }, [previewMode]);

  const toggleDemoMode = useCallback(() => {
    setDemoMode(!demoMode);
  }, [demoMode, setDemoMode]);

  useEffect(() => {
    if (!previewMode) {
      writeDemoMode(demoMode);
    }
  }, [demoMode, previewMode]);

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
