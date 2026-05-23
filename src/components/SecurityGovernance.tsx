import React, { useState, useEffect, useRef } from "react";
import { 
  ShieldCheck, 
  RotateCw, 
  Lock, 
  Key, 
  FileText, 
  CheckCircle,
  AlertTriangle
} from "lucide-react";
import { LogItem, ThreatPoint } from "../types";

export const SecurityGovernance: React.FC = () => {
  const [keyRotated, setKeyRotated] = useState(false);
  const [isRotating, setIsRotating] = useState(false);
  const [currentHash, setCurrentHash] = useState("pq_sha384_7ce89aab2f10b0e774f8a002bc0f");
  const [complianceScore, setComplianceScore] = useState(99.4);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Generate simulated ZKP and blockchain logs
  useEffect(() => {
    const baseLogs: LogItem[] = [
      { id: 1, type: "zkp", message: "ZKP verification passed: Node SM-PRV-3 verified trade authorization", severity: "success", timestamp: Date.now() - 5000, iconName: "ShieldCheck", color: "green" },
      { id: 2, type: "blockchain", message: "Block 481,209 generated securely. 47 transactions appended.", severity: "success", timestamp: Date.now() - 15000, iconName: "FileText", color: "blue" },
      { id: 3, type: "key", message: "Decentralized consensus approved rotating quantum key parameters", severity: "info", timestamp: Date.now() - 30000, iconName: "Key", color: "purple" }
    ];
    setLogs(baseLogs);

    const timer = setInterval(() => {
      const isZkp = Math.random() > 0.5;
      const nextLog: LogItem = isZkp ? {
        id: Date.now(),
        type: "zkp",
        message: `ZKP proof verified successfully. Proof hash: ${Math.random().toString(16).substring(2, 10)}...`,
        severity: "success",
        timestamp: Date.now(),
        iconName: "ShieldCheck",
        color: "green"
      } : {
        id: Date.now(),
        type: "blockchain",
        message: `AppendTransaction: Immutable ledger recorded ${Math.floor(Math.random() * 20) + 5} consensus receipts.`,
        severity: "success",
        timestamp: Date.now(),
        iconName: "FileText",
        color: "blue"
      };

      setLogs(prev => [nextLog, ...prev.slice(0, 5)]);
    }, 6000);

    return () => clearInterval(timer);
  }, []);

  // Post quantum key rotation simulation
  const rotateQuantumKeys = () => {
    setIsRotating(true);
    setKeyRotated(false);

    // Dynamic rotation simulation
    setTimeout(() => {
      const nextHashArr = Array.from({ length: 6 }, () => Math.random().toString(16).substring(2, 6));
      const newKeyHash = `pq_sha384_${nextHashArr.join("")}`;
      setCurrentHash(newKeyHash);
      setIsRotating(false);
      setKeyRotated(true);
      setComplianceScore(99.8);

      // Add to log list
      const rotationLog: LogItem = {
        id: Date.now(),
        type: "key",
        message: `POST-QUANTUM KEY ROTATED SECURELY. New system hash: ${newKeyHash}`,
        severity: "success",
        timestamp: Date.now(),
        iconName: "Key",
        color: "purple"
      };
      setLogs(prev => [rotationLog, ...prev.slice(0, 5)]);
    }, 2500);
  };

  // Canvas Vector Grid representing security threat maps
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const { width, height } = rect;
    let animationId: number;
    let scanLineY = 0;

    const threats: ThreatPoint[] = [
      { id: 1, x: width * 0.25, y: height * 0.4, severity: 2, type: "fraud" },
      { id: 2, x: width * 0.65, y: height * 0.35, severity: 1, type: "anomaly" },
      { id: 3, x: width * 0.45, y: height * 0.75, severity: 1, type: "intrusion" }
    ];

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Radar rings
      ctx.strokeStyle = "rgba(255, 255, 255, 0.06)";
      ctx.lineWidth = 1;
      const center = { x: width / 2, y: height / 2 };
      for (let r = 30; r < Math.max(width, height); r += 40) {
        ctx.beginPath();
        ctx.arc(center.x, center.y, r, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Threats render
      threats.forEach((th) => {
        const pulse = Math.sin(Date.now() * 0.005 + th.id) * 3 + 6;
        ctx.beginPath();
        ctx.arc(th.x, th.y, pulse, 0, Math.PI * 2);
        ctx.fillStyle = th.severity > 1 ? "rgba(255, 255, 255, 0.12)" : "rgba(255, 255, 255, 0.06)";
        ctx.fill();

        ctx.beginPath();
        ctx.arc(th.x, th.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.75)";
        ctx.fill();

        // Label
        ctx.font = "9px monospace";
        ctx.fillStyle = "rgba(255,255,255,0.4)";
        ctx.fillText(`VECTOR: ${th.type.toUpperCase()}`, th.x + 8, th.y + 3);
      });

      // Scanline
      ctx.beginPath();
      ctx.moveTo(0, scanLineY);
      ctx.lineTo(width, scanLineY);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
      ctx.lineWidth = 1;
      ctx.stroke();

      scanLineY = (scanLineY + 1) % height;
      animationId = requestAnimationFrame(draw);
    };

    draw();

    return () => cancelAnimationFrame(animationId);
  }, []);

  return (
    <div className="space-y-6">
      {/* Head */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Security & Compliance</h1>
          <p className="text-white/40 text-xs mt-1 font-light">Impenetrable Zero-Knowledge Cryptography and sovereign regulatory compliance mapping</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs">
          <ShieldCheck className="w-3.5 h-3.5 text-white/60" />
          <span className="text-white/60 font-medium">COMPLIANCE DECREE: CERTIFIED ({complianceScore}%)</span>
        </div>
      </div>

      {keyRotated && (
        <div className="bg-white/5 border border-white/15 text-white/95 px-4 py-3 rounded text-sm flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-white/75" />
          <div>
            <span className="font-bold mr-1">Rotation Complete!</span> System keys rotated to post-quantum safe boundaries. Current Hash: 
            <span className="font-mono text-xs block text-white/80 mt-0.5">{currentHash}</span>
          </div>
        </div>
      )}

      {/* Main security grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Verification ledger (left colspan: 2) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Main Key controller area */}
          <div className="metric-card rounded p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 border-white/10">
            <div className="space-y-2 max-w-sm">
              <h3 className="text-base font-serif italic text-white flex items-center font-normal">
                <Lock className="w-4 h-4 mr-2 text-white/50" />
                Sovereign Quantum Shields
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed font-sans">
                PRIV Core safeguards all treasury allocations and filings with Kyber and Dilithium post-quantum security algorithms.
              </p>
              
              <div className="pt-2">
                <div className="text-[10px] font-mono text-gray-400">CURRENT PQ CORE HASH:</div>
                <div className="font-mono text-[11px] text-white/80 break-all select-all font-bold mt-1 bg-neutral-900/40 p-2.5 border border-white/5 rounded leading-relaxed">
                  {currentHash}
                </div>
              </div>
            </div>

            <div className="flex-shrink-0">
              <button 
                onClick={rotateQuantumKeys}
                disabled={isRotating}
                className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-medium text-xs px-5 py-4 rounded transition flex items-center justify-center space-x-2 border border-white cursor-pointer"
              >
                <RotateCw className={`w-4 h-4 text-neutral-950 ${isRotating ? "animate-spin" : ""}`} />
                <span>{isRotating ? "RECOMPUTING SHARING HASHES..." : "ROTATE SECURE REGULATORY KEYS"}</span>
              </button>
            </div>
          </div>

          {/* Core logs */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <FileText className="w-4 h-4 mr-2 text-white/50" />
              Immutable Cryptographic Ledger Nodes
            </h3>

            <div className="space-y-3.5 max-h-[280px] overflow-y-auto scrollbar-hide">
              {logs.map(log => (
                <div key={log.id} className="p-3 bg-neutral-900/30 border border-white/5 rounded flex items-center justify-between text-xs transition duration-200 hover:border-white/10">
                  <div className="flex items-center space-x-3">
                    <div className="w-1.5 h-1.5 bg-white/70 rounded-full animate-pulse flex-shrink-0" />
                    <div>
                      <p className="font-sans text-gray-300 leading-snug">{log.message}</p>
                      <p className="text-[9px] font-mono text-gray-500 mt-1 uppercase">TYPE: {log.type} // AUTH: TRUSTED</p>
                    </div>
                  </div>
                  <div className="text-[9px] font-mono text-gray-500 whitespace-nowrap ml-2">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Threat Anomaly radar screen */}
        <div className="metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <AlertTriangle className="w-4 h-4 mr-2 text-white/50" />
              Sovereign Intrusion Matrix
            </h3>
            <p className="text-xs text-stone-400 mb-4 col-description">
              Continuous spatial monitoring of simulated endpoint security and cross-border API latency sweeps.
            </p>
          </div>

          <div className="relative bg-neutral-950/40 rounded overflow-hidden border border-white/10">
            <canvas ref={canvasRef} className="w-full h-48 block" />
            <div className="absolute bottom-2 left-2 text-[8px] font-mono text-white/70 flex items-center space-x-1 px-2 py-0.5 bg-white/5 rounded border border-white/10">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping" />
              <span>IP DEFENSE SHIELD: DUAL MODE ACTIVE</span>
            </div>
          </div>

          <div className="text-[11px] font-mono text-gray-500 mt-5 space-y-1.5 border-t border-white/10 pt-4">
            <div className="flex justify-between">
              <span>ACTIVE THREAT LEVEL:</span>
              <span className="text-white font-medium uppercase">Optimal</span>
            </div>
            <div className="flex justify-between">
              <span>ENCRYPTION INDEX:</span>
              <span className="text-white/60 font-mono">512-bit sha3-ecc</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
