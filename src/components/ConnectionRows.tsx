import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

// Row components extracted to module level: calling hooks inside a
// .map() callback changes hook count whenever the list length changes
// and crashes React (#310 "Rendered more hooks than during the previous
// render"). Each row owns a stable hook set here instead.

export interface TaxPortal {
  id: string;
  name: string;
  location: string;
  desc: string;
}

export function TaxPortalRow({ tax }: { tax: TaxPortal }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isConnected, setIsConnected] = useState(() => {
    try {
      return localStorage.getItem(`tax_conn_${tax.id}`) === "true";
    } catch {
      return false;
    }
  });
  const [isPending, setIsPending] = useState(false);
  const [step, setStep] = useState("");

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    setIsPending(true);
    setStep("Initiating secure SSL handshake to tax authority...");
    setTimeout(() => {
      setStep("Bypassing 2FA firewall protocols...");
      setTimeout(() => {
        setStep("Synchronizing structural corporate guidelines...");
        setTimeout(() => {
          setIsPending(false);
          setStep("");
          setIsConnected(true);
          try {
            localStorage.setItem(`tax_conn_${tax.id}`, "true");
          } catch {
            /* ignore */
          }
        }, 1000);
      }, 800);
    }, 800);
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    try {
      localStorage.removeItem(`tax_conn_${tax.id}`);
    } catch {
      /* ignore */
    }
    setUsername("");
    setPassword("");
  };

  return (
    <div className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10 text-xs">
      <div className="flex items-center justify-between animate-fadeIn">
        <div>
          <h4 className="text-xs font-mono font-bold text-white">{tax.name}</h4>
          <span className="text-[10px] text-zinc-500 leading-none block mt-0.5">{tax.location} &bull; {tax.desc}</span>
        </div>
        <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
          isConnected
            ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/20"
            : "bg-neutral-900 text-stone-500 border-white/5"
        }`}>
          {isConnected ? "CONNECTED (Live Feed)" : "NOT CONNECTED"}
        </span>
      </div>

      {isConnected ? (
        <div className="flex items-center justify-between bg-emerald-500/5 border border-emerald-500/10 p-2 rounded text-[10px] font-mono text-emerald-400">
          <span>Authorized asset synchronization & tax filing pathways secure.</span>
          <button onClick={handleDisconnect} className="text-stone-400 hover:text-white underline text-[9.5px] cursor-pointer">
            DISCONNECT
          </button>
        </div>
      ) : isPending ? (
        <div className="p-3 border border-orange-500/20 bg-orange-500/5 text-orange-400 text-[10px] font-mono rounded animate-pulse">
          {step}
        </div>
      ) : (
        <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono">
          <input
            type="text"
            placeholder="Portal ID / User"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
            required
          />
          <input
            type="password"
            placeholder="Secret Passkey"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
            required
          />
          <button
            type="submit"
            className="bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer"
          >
            SIGN INTO PLATFORM
          </button>
        </form>
      )}
    </div>
  );
}

export interface ExchangeInfo {
  id: string;
  name: string;
  desc: string;
  defaultBal: string;
}

export function ExchangeRow({ ex }: { ex: ExchangeInfo }) {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [isConnected, setIsConnected] = useState(() => {
    try {
      return localStorage.getItem(`ex_conn_${ex.id}`) === "true";
    } catch {
      return false;
    }
  });
  const [isPending, setIsPending] = useState(false);
  const [step, setStep] = useState("");

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey || !apiSecret) return;
    setIsPending(true);
    setStep("Handshaking Secure Websocket endpoint...");
    setTimeout(() => {
      setStep("Retrieving verified API keys rights (Spot, Leverage active)...");
      setTimeout(() => {
        setStep("Linking trading lots to PRIV automated pipeline...");
        setTimeout(() => {
          setIsPending(false);
          setStep("");
          setIsConnected(true);
          try {
            localStorage.setItem(`ex_conn_${ex.id}`, "true");
          } catch {
            /* ignore */
          }
          navigate("/dashboard/profile?triggerKYC=true");
        }, 1000);
      }, 800);
    }, 800);
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    try {
      localStorage.removeItem(`ex_conn_${ex.id}`);
    } catch {
      /* ignore */
    }
    setApiKey("");
    setApiSecret("");
  };

  return (
    <div className="p-4 border border-white/5 rounded bg-black/40 space-y-3.5 transition hover:border-white/10 text-xs">
      <div className="flex items-center justify-between animate-fadeIn">
        <div>
          <h4 className="text-xs font-mono font-bold text-white mb-0.5">{ex.name}</h4>
          <span className="text-[10px] text-zinc-550 leading-none block">{ex.desc}</span>
        </div>
        <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${
          isConnected
            ? "bg-sky-500/5 text-sky-400 border-sky-500/20"
            : "bg-neutral-900 text-stone-500 border-white/5"
        }`}>
          {isConnected ? `ACTIVE SYNC` : "NOT CONNECTED"}
        </span>
      </div>

      {isConnected ? (
        <div className="flex items-center justify-between bg-sky-500/5 border border-sky-500/10 p-2.5 rounded text-[10px] font-mono text-sky-400">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 bg-sky-400 rounded-full animate-ping" />
            Connected &bull; Active Reserves: <strong className="text-white">{ex.defaultBal}</strong> ready for auto-arbitrage.
          </span>
          <button onClick={handleDisconnect} className="text-stone-300 hover:text-white underline text-[9.5px] cursor-pointer">
            DISCONNECT
          </button>
        </div>
      ) : isPending ? (
        <div className="p-3 border border-sky-500/20 bg-sky-500/5 text-sky-400 text-[10px] font-mono rounded animate-pulse">
          {step}
        </div>
      ) : (
        <form onSubmit={handleConnect} className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 font-mono">
          <input
            type="text"
            placeholder="API Access Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
            required
          />
          <input
            type="password"
            placeholder="API Secret Token"
            value={apiSecret}
            onChange={(e) => setApiSecret(e.target.value)}
            className="bg-neutral-955 border border-white/10 rounded p-1.5 text-[10px] text-white focus:outline-none focus:border-white/30"
            required
          />
          <button
            type="submit"
            className="bg-sky-450 hover:bg-sky-500 text-black font-bold text-[10px] py-1.5 px-3 rounded text-center transition cursor-pointer"
          >
            SYNC WITH BINANCE
          </button>
        </form>
      )}
    </div>
  );
}
