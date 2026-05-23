import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export default function BrokerOAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const broker = params.get('broker') || 'unknown';
  const status = params.get('status') || 'unknown';
  const message = params.get('message') || '';
  const [countdown, setCountdown] = useState(5);

  const success = status === 'success';

  useEffect(() => {
    if (countdown <= 0) {
      navigate('/dashboard/broker-connect');
      return;
    }
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown, navigate]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6">
      <div className="metric-card max-w-md w-full p-8 rounded-xl border border-white/10 text-center">
        {success ? (
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        ) : (
          <XCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
        )}
        <h1 className="text-xl font-serif italic text-white mb-2">
          {success ? 'Broker connected' : 'Connection failed'}
        </h1>
        <p className="text-white/50 text-sm font-mono mb-4">
          {broker.toUpperCase()} — {status}
          {message && ` (${message})`}
        </p>
        {success ? (
          <p className="text-emerald-400/80 text-xs mb-6">
            Priv can now pull positions and run market analysis on this account.
          </p>
        ) : (
          <p className="text-amber-400/80 text-xs mb-6">
            Try API key connect or check OAuth configuration (DERIV_APP_ID, ALPACA_OAUTH_CLIENT_ID).
          </p>
        )}
        <div className="flex items-center justify-center gap-2 text-white/40 text-xs font-mono mb-4">
          <Loader2 className="w-3 h-3 animate-spin" />
          Redirecting in {countdown}s…
        </div>
        <Link
          to="/dashboard/broker-connect"
          className="inline-block px-4 py-2 rounded border border-white/20 text-white text-sm hover:bg-white/10"
        >
          Back to Broker Connect
        </Link>
      </div>
    </div>
  );
}
