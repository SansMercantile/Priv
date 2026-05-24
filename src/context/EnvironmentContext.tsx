import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { toast } from '../components/ui/use-toast';
import { readDemoMode, writeDemoMode } from '../lib/environment';

export type EnvironmentType = 'demo' | 'live';

export interface EnvironmentRequirements {
  requiresKYC: boolean;
  requiresProfileCompletion: boolean;
  requiresBrokerConnection: boolean;
  mockDataAvailable: boolean;
  realTimeDataAvailable: boolean;
}

interface EnvironmentContextValue {
  demoMode: boolean;
  environmentType: EnvironmentType;
  setDemoMode: (enabled: boolean) => void;
  toggleDemoMode: () => void;
  getEnvironmentRequirements: () => EnvironmentRequirements;
  isReady: boolean;
  lastToggleTime: number;
}

const EnvironmentContext = createContext<EnvironmentContextValue | null>(null);

export function EnvironmentProvider({ children }: { children: React.ReactNode }) {
  const [demoMode, setDemoModeState] = useState<boolean>(() => readDemoMode());
  const [isReady, setIsReady] = useState(false);
  const [lastToggleTime, setLastToggleTime] = useState(Date.now());

  const environmentType: EnvironmentType = demoMode ? 'demo' : 'live';

  const getEnvironmentRequirements = useCallback((): EnvironmentRequirements => {
    if (demoMode) {
      return {
        requiresKYC: false,
        requiresProfileCompletion: false,
        requiresBrokerConnection: false,
        mockDataAvailable: true,
        realTimeDataAvailable: false,
      };
    }
    // Live environment requirements
    return {
      requiresKYC: true,
      requiresProfileCompletion: true,
      requiresBrokerConnection: true,
      mockDataAvailable: false,
      realTimeDataAvailable: true,
    };
  }, [demoMode]);

  const setDemoMode = useCallback((enabled: boolean) => {
    setDemoModeState(enabled);
    setLastToggleTime(Date.now());
    writeDemoMode(enabled);
    
    const toastConfig = enabled
      ? {
          title: '🎭 DEMO MODE ACTIVATED',
          description:
            'You are now in Demo Mode. Sample portfolios, simulated data, and free public market data (delayed ~15 min) are available. No KYC or account setup required.',
          duration: 8000,
        }
      : {
          title: '🔒 LIVE MODE ACTIVATED',
          description:
            'You have switched to Live Mode. Complete KYC verification, customize your profile, and connect a real trading broker to enable live market analysis and trading.',
          duration: 8000,
        };
    
    toast(toastConfig);
  }, []);

  const toggleDemoMode = useCallback(() => {
    setDemoMode(!demoMode);
  }, [demoMode, setDemoMode]);

  useEffect(() => {
    writeDemoMode(demoMode);
    // Simulate ready state after a brief delay
    const timer = setTimeout(() => setIsReady(true), 300);
    return () => clearTimeout(timer);
  }, [demoMode]);

  const value = useMemo(
    () => ({
      demoMode,
      environmentType,
      setDemoMode,
      toggleDemoMode,
      getEnvironmentRequirements,
      isReady,
      lastToggleTime,
    }),
    [demoMode, environmentType, setDemoMode, toggleDemoMode, getEnvironmentRequirements, isReady, lastToggleTime]
  );

  return <EnvironmentContext.Provider value={value}>{children}</EnvironmentContext.Provider>;
}

export function useEnvironment(): EnvironmentContextValue {
  const ctx = useContext(EnvironmentContext);
  if (!ctx) {
    throw new Error('useEnvironment must be used within EnvironmentProvider');
  }
  return ctx;
}
