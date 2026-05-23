import React from 'react';
import { AlertTriangle, Sparkles, X } from 'lucide-react';
import { useEnvironment } from '../context/EnvironmentContext';

interface DemoEnvironmentNoticeProps {
  onDismiss?: () => void;
  dismissed?: boolean;
}

export default function DemoEnvironmentNotice({ onDismiss, dismissed }: DemoEnvironmentNoticeProps) {
  const { demoMode, toggleDemoMode } = useEnvironment();

  if (!demoMode || dismissed) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 border-b border-amber-500/40 bg-gradient-to-r from-amber-950/95 via-orange-950/90 to-amber-950/95 backdrop-blur-md"
      role="status"
      aria-live="polite"
    >
      <div className="mx-auto flex max-w-6xl items-start gap-3 px-4 py-3 text-amber-50">
        <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" aria-hidden />
        <div className="min-w-0 flex-1 text-sm">
          <p className="font-semibold tracking-wide">Demo environment active</p>
          <p className="mt-0.5 text-xs text-amber-100/90 leading-relaxed">
            You are viewing simulated data only — delayed public market feeds, sample portfolios, and mock audit logs.
            Create a real Priv account, complete KYC, and connect a live or broker demo trading account to use production analysis.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={toggleDemoMode}
            className="rounded border border-amber-400/50 bg-amber-500/20 px-3 py-1 text-[11px] font-mono font-semibold uppercase tracking-wider text-amber-50 hover:bg-amber-500/30"
          >
            Switch to live
          </button>
          {onDismiss && (
            <button
              type="button"
              onClick={onDismiss}
              className="rounded p-1 text-amber-200/80 hover:bg-white/10 hover:text-white"
              aria-label="Dismiss demo notice"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      <div className="flex items-center justify-center gap-1 border-t border-amber-500/20 bg-amber-900/30 py-0.5 text-[10px] font-mono text-amber-200/70">
        <AlertTriangle className="h-3 w-3" />
        <span>Not for investment decisions · Sample data only</span>
      </div>
    </div>
  );
}
