/**
 * DemoEnvironmentNotification
 * Enhanced notification modal for demo mode
 * Displays when user enters demo mode with feature limitations and upgrade path
 */

import React, { useState, useEffect } from 'react';
import { AlertCircle, Zap, Shield, BarChart3, X } from 'lucide-react';

interface DemoEnvironmentNotificationProps {
  visible: boolean;
  onClose: () => void;
  demoMode: boolean;
}

export default function DemoEnvironmentNotification({
  visible,
  onClose,
  demoMode,
}: DemoEnvironmentNotificationProps) {
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    if (visible) {
      setTimeout(() => setAnimate(true), 50);
    } else {
      setAnimate(false);
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300 ${
          animate ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 max-w-2xl w-full mx-4 transition-all duration-300 ${
          animate ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`}
      >
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl border border-orange-500/30 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-orange-600 to-orange-500 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-white" />
              <h2 className="text-xl font-bold text-white">
                {demoMode ? '🎭 Demo Mode Active' : '🔒 Live Mode'}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-lg p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-6">
            {demoMode ? (
              <>
                <p className="text-slate-300 mb-6 leading-relaxed">
                  You're exploring Priv in <span className="font-semibold text-orange-400">demo mode</span>. This environment gives you a risk-free way to explore all the powerful features of our AI-driven trading platform.
                </p>

                {/* Features Available */}
                <div className="mb-8">
                  <h3 className="text-sm font-semibold text-slate-200 mb-4 uppercase tracking-wider">Available in Demo Mode:</h3>
                  <div className="space-y-3">
                    <FeatureItem
                      icon={<Zap className="w-4 h-4" />}
                      title="Simulated Trading"
                      description="Execute trades on demo capital with paper trading"
                    />
                    <FeatureItem
                      icon={<BarChart3 className="w-4 h-4" />}
                      title="Market Data"
                      description="Real market data (delayed ~15 minutes) from public sources"
                    />
                    <FeatureItem
                      icon={<Shield className="w-4 h-4" />}
                      title="AI-Powered Analysis"
                      description="Full access to our 12+ AI agents and analysis tools"
                    />
                  </div>
                </div>

                {/* Limitations */}
                <div className="mb-8 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-slate-200 mb-3 uppercase tracking-wider">Not Available in Demo:</h3>
                  <ul className="text-sm text-slate-400 space-y-2">
                    <li>✗ Real account trading and money management</li>
                    <li>✗ Live broker account connections</li>
                    <li>✗ Real-time market data (less than 5 minutes)</li>
                    <li>✗ Regulatory compliance and KYC verification</li>
                  </ul>
                </div>

                {/* CTA */}
                <div className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border border-blue-500/30 rounded-lg p-4 mb-6">
                  <p className="text-sm text-slate-300">
                    Ready to go live? Create a real account, complete KYC verification, and connect your broker to unlock unlimited trading potential.
                  </p>
                </div>
              </>
            ) : (
              <>
                <p className="text-slate-300 mb-6 leading-relaxed">
                  You're now in <span className="font-semibold text-green-400">live mode</span>. To start trading with real market data and broker connections, you need to:
                </p>

                <div className="space-y-3 mb-8">
                  <StepItem number={1} title="Verify Your Identity" description="Complete KYC verification with government-issued ID" />
                  <StepItem number={2} title="Customize Your Profile" description="Add trading knowledge, appetite, and goals" />
                  <StepItem number={3} title="Connect Your Broker" description="Link a real or paper trading account from your broker" />
                  <StepItem number={4} title="Start Trading" description="Begin live trading with real-time market analysis" />
                </div>

                <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 border border-green-500/30 rounded-lg p-4">
                  <p className="text-sm text-slate-300">
                    Your Priv account is secure and compliant with all regulatory requirements. Your data is encrypted and protected.
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="bg-slate-800/50 border-t border-slate-700 px-6 py-4 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg font-medium text-slate-300 hover:bg-slate-700 transition-colors"
            >
              Got it
            </button>
            {demoMode && (
              <button className="px-4 py-2 rounded-lg font-medium bg-gradient-to-r from-orange-600 to-orange-500 text-white hover:shadow-lg hover:shadow-orange-500/50 transition-all">
                Upgrade to Live
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

interface FeatureItemProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

function FeatureItem({ icon, title, description }: FeatureItemProps) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 text-orange-400 mt-1">{icon}</div>
      <div className="flex-1">
        <p className="font-semibold text-slate-200 text-sm">{title}</p>
        <p className="text-slate-400 text-sm">{description}</p>
      </div>
    </div>
  );
}

interface StepItemProps {
  number: number;
  title: string;
  description: string;
}

function StepItem({ number, title, description }: StepItemProps) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600/30 border border-green-500/50 flex items-center justify-center font-semibold text-green-400 text-sm">
        {number}
      </div>
      <div className="flex-1 pt-1">
        <p className="font-semibold text-slate-200 text-sm">{title}</p>
        <p className="text-slate-400 text-sm">{description}</p>
      </div>
    </div>
  );
}
