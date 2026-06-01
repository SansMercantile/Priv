import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, ArrowRight, RefreshCw } from 'lucide-react';

const XMBridge = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<'idle' | 'waiting' | 'success'>('idle');

  useEffect(() => {
    // Poll the server to see if the session has been captured via the siphon
    const interval = setInterval(async () => {
      try {
        const activeId = localStorage.getItem("xm_account_id");
        if (activeId) {
          const res = await fetch(`/api/brokers/registered/xm_user_account_${activeId}`);
          const data = await res.json();
          if (data.broker && data.broker.session_validated) {
            setStatus('success');
            clearInterval(interval);
            setTimeout(() => navigate('/dashboard/terminal'), 2000);
          }
        }
      } catch (e) {
        console.error("Bridge polling error:", e);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [navigate]);

  const handleLoginClick = () => {
    setStatus('waiting');
    // Open XM login in a new window
    window.open('https://my.xm.com/member/login', 'xmLogin', 'width=600,height=800');
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6 font-mono">
      <div className="max-w-md w-full bg-neutral-950 border border-white/10 rounded-2xl p-8 space-y-8 shadow-2xl text-center">
        <div className="flex justify-center">
          <div className="p-4 bg-emerald-500/10 rounded-full border border-emerald-500/20">
            <Lock className="w-8 h-8 text-emerald-400" />
          </div>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-serif italic text-white">Secure XM Handshake</h1>
          <p className="text-zinc-400 text-xs leading-relaxed">
            You are being routed through the SANS Secure Bridge. Please sign in to your XM account to synchronize your live ledger.
          </p>
        </div>

        {status === 'idle' && (
          <button 
            onClick={handleLoginClick}
            className="w-full py-4 bg-white text-black font-bold text-xs rounded-lg hover:bg-zinc-200 transition-all flex items-center justify-center gap-2 group"
          >
            SIGN IN TO XM
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        )}

        {status === 'waiting' && (
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-3 p-4 bg-neutral-900 rounded-lg border border-white/5">
              <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
              <span className="text-xs text-zinc-300">Waiting for XM Authentication...</span>
            </div>
            <p className="text-[10px] text-zinc-500">
              Once you have logged in to XM, our bridge will automatically detect the session and return you to the terminal.
            </p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="flex items-center justify-center gap-3 p-4 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400 font-bold">SESSION CAPTURED</span>
            </div>
            <p className="text-xs text-zinc-400">Redirecting you back to the Execution Engine...</p>
          </div>
        )}

        <div className="pt-6 border-t border-white/5">
          <button 
            onClick={() => navigate('/dashboard/terminal')}
            className="text-[10px] text-zinc-500 hover:text-white transition-colors underline"
          >
            Cancel and return to Terminal
          </button>
        </div>
      </div>
    </div>
  );
};

export default XMBridge;
