import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import { getSessionUserId } from '../lib/environment';
import { Plug, Key, ExternalLink } from 'lucide-react';

function BrokerConnectionCard({ brokerName, affiliateUrl, demoMode }) {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [message, setMessage] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleConnect = async (e) => {
    e.preventDefault();
    if (demoMode) {
      setMessage({ type: 'success', text: 'Demo mode — API keys not persisted.' });
      return;
    }
    setIsSaving(true);
    setMessage(null);
    try {
      const response = await apiClient.connectBroker({
        broker_name: brokerName,
        api_key: apiKey,
        api_secret: apiSecret,
      });
      setMessage({ type: 'success', text: response.message || 'Connected' });
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="metric-card p-6 rounded border border-white/10">
      <h3 className="text-lg font-serif italic text-white mb-4">{brokerName}</h3>
      <a
        href={affiliateUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full py-2 mb-4 rounded border border-white/20 text-white/80 text-sm hover:bg-white/5"
      >
        <ExternalLink className="w-4 h-4" /> Open broker signup
      </a>
      <form onSubmit={handleConnect} className="space-y-3">
        <input
          type="text"
          placeholder="API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full p-2.5 rounded bg-neutral-900 border border-white/10 text-white text-sm font-mono"
          required={!demoMode}
        />
        <input
          type="password"
          placeholder="API Secret"
          value={apiSecret}
          onChange={(e) => setApiSecret(e.target.value)}
          className="w-full p-2.5 rounded bg-neutral-900 border border-white/10 text-white text-sm font-mono"
          required={!demoMode}
        />
        <button
          type="submit"
          disabled={isSaving}
          className="w-full py-2.5 rounded bg-white/10 border border-white/20 text-white text-sm font-mono font-semibold hover:bg-white/15 disabled:opacity-50"
        >
          {isSaving ? 'Connecting…' : 'Connect with API keys'}
        </button>
        {message && (
          <p className={`text-xs text-center font-mono ${message.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
            {message.text}
          </p>
        )}
      </form>
    </div>
  );
}

function OAuthBrokerCard({ broker, demoMode }) {
  const startOAuth = (accountType) => {
    if (demoMode) {
      alert(`Demo mode: OAuth to ${broker.name} is simulated. Switch to live and set ${broker.id} credentials in backend .env.`);
      return;
    }
    if (!getSessionUserId()) {
      alert('Sign in first so Priv can associate this broker with your account.');
      return;
    }
    if (!broker.configured && broker.auth_type === 'oauth') {
      alert(`${broker.name} OAuth is not configured on the server.`);
      return;
    }
    window.location.href = apiClient.getOAuthLoginUrl(broker.id, accountType);
  };

  return (
    <div className="metric-card p-6 rounded border border-emerald-500/20">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-serif italic text-white">{broker.name}</h3>
        <span className="text-[9px] font-mono uppercase px-2 py-0.5 rounded border border-white/10 text-white/50">
          {broker.auth_type}
        </span>
      </div>
      {broker.note && <p className="text-xs text-white/40 mb-3">{broker.note}</p>}
      {broker.auth_type === 'oauth' ? (
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => startOAuth(broker.supports_demo ? 'demo' : 'paper')}
            className="w-full py-2.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-sm font-mono hover:bg-emerald-500/30"
          >
            Connect {broker.supports_demo ? 'demo' : 'paper'} account (OAuth)
          </button>
          {broker.supports_live && (
            <button
              type="button"
              onClick={() => startOAuth('live')}
              className="w-full py-2.5 rounded bg-white/5 border border-white/15 text-white/80 text-sm font-mono hover:bg-white/10"
            >
              Connect live account (OAuth)
            </button>
          )}
        </div>
      ) : (
        <p className="text-xs text-white/50 font-mono">Use API key form below for this broker.</p>
      )}
    </div>
  );
}

export default function ConnectionsPage({ demoMode = false }) {
  const [oauthBrokers, setOauthBrokers] = useState([]);
  const [connections, setConnections] = useState([]);

  useEffect(() => {
    if (demoMode) {
      setOauthBrokers([
        { id: 'deriv', name: 'Deriv', auth_type: 'oauth', configured: true, supports_demo: true, supports_live: true },
      ]);
      return;
    }
    (async () => {
      try {
        const b = await apiClient.getOAuthBrokers();
        setOauthBrokers(b?.brokers || b?.data?.brokers || []);
        const c = await apiClient.getOAuthConnections();
        setConnections(c?.connections || c?.data?.connections || []);
      } catch (e) {
        console.warn(e);
      }
    })();
  }, [demoMode]);

  const xmAffiliateLink = 'https://clicks.pipaffiliates.com/c?c=YOUR_CODE&l=en&p=1';

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-serif italic text-white flex items-center gap-3">
          <Plug className="w-8 h-8 text-white/70" />
          Broker Connect
        </h1>
        <p className="text-white/40 text-xs mt-2 max-w-2xl font-light">
          Link a live or broker-provided demo account via OAuth or API keys. Priv uses this for market analysis, risk, and execution routing.
        </p>
      </div>

      {connections.length > 0 && (
        <div className="metric-card p-4 rounded border border-emerald-500/30">
          <h3 className="text-sm font-mono text-emerald-400 mb-2">Active OAuth connections</h3>
          <ul className="space-y-1">
            {connections.map((c, i) => (
              <li key={i} className="text-xs font-mono text-white/70 flex justify-between">
                <span>{c.broker} ({c.account_type})</span>
                <span className="text-emerald-400">{c.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <section>
        <h2 className="text-sm font-mono text-white/50 uppercase tracking-widest mb-4 flex items-center gap-2">
          <Key className="w-4 h-4" /> OAuth brokers
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {oauthBrokers.map((b) => (
            <OAuthBrokerCard key={b.id} broker={b} demoMode={demoMode} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-mono text-white/50 uppercase tracking-widest mb-4">API key brokers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <BrokerConnectionCard brokerName="XM Global" affiliateUrl={xmAffiliateLink} demoMode={demoMode} />
          <BrokerConnectionCard brokerName="Binance" affiliateUrl="https://www.binance.com" demoMode={demoMode} />
        </div>
      </section>
    </div>
  );
}
