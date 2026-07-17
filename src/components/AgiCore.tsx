import React, { useState, useEffect, useRef } from "react";
import { Brain, Sparkles, Heart, RefreshCw, Cpu, Gauge } from "lucide-react";

interface Metrics {
  empathy_score: number;
  coherence: number;
  decision_latency_ms: number;
  strategic_coherence: number;
}

export const AgiCore: React.FC<{ demoMode?: boolean }> = () => {
  const [altruism, setAltruism] = useState(84);
  const [caution, setCaution] = useState(72);
  const [intuition, setIntuition] = useState(91);
  const [stability, setStability] = useState(95);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("/api/v1/agi/status");
        const data = await res.json();
        if (res.ok) {
          const d = data.data || data;
          if (d.params) {
            setAltruism(d.params.altruism);
            setCaution(d.params.caution);
            setIntuition(d.params.intuition);
            setStability(d.params.stability);
          }
          if (d.metrics) setMetrics(d.metrics);
        } else {
          setError(data.detail || "AGI Core status unavailable.");
        }
      } catch (err: any) {
        setError(err.message || "AGI Core status unavailable.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const saveParams = async (params: { altruism: number; caution: number; intuition: number; stability: number }) => {
    setSaving(true);
    try {
      const res = await fetch("/api/v1/agi/emotional-params", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (res.ok) {
        const d = data.data || data;
        if (d.metrics) setMetrics(d.metrics);
        setError(null);
      } else {
        setError(data.detail || "Failed to save parameters.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to save parameters.");
    } finally {
      setSaving(false);
    }
  };

  const commit = (next: { altruism: number; caution: number; intuition: number; stability: number }) => {
    saveParams(next);
  };

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
    let animationFrameId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
      ctx.lineWidth = 1;
      const step = 20;
      for (let x = 0; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
      const waveLayers = [
        { amplitude: 35, freq: 0.008, speed: 0.05, stroke: "rgba(255, 255, 255, 0.4)", width: 2 },
        { amplitude: 20, freq: 0.015, speed: -0.07, stroke: "rgba(163, 163, 163, 0.3)", width: 1.5 },
      ];
      waveLayers.forEach((layer) => {
        ctx.beginPath();
        ctx.strokeStyle = layer.stroke;
        ctx.lineWidth = layer.width;
        for (let x = 0; x < width; x++) {
          const y = height / 2 + Math.sin(x * layer.freq + phase * layer.speed) * layer.amplitude * (stability / 100);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      });
      phase += 0.5;
      animationFrameId = requestAnimationFrame(render);
    };
    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [stability]);

  const Slider = ({
    label, value, setValue, lowLabel, highLabel,
  }: { label: string; value: number; setValue: (n: number) => void; lowLabel: string; highLabel: string }) => (
    <div className="space-y-2 mb-5">
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-gray-300">{label}</span>
        <span className="text-white font-bold font-mono">{value}%</span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
        onMouseUp={() => commit({ altruism, caution, intuition, stability })}
        onTouchEnd={() => commit({ altruism, caution, intuition, stability })}
        className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
      />
      <div className="flex justify-between text-[9px] text-gray-500 font-mono">
        <span>{lowLabel}</span>
        <span>{highLabel}</span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white">AGI Core Intelligence</h1>
          <p className="text-white/40 text-xs font-light mt-1">Decision-alignment parameters governing Priv's autonomous execution behavior</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10">
          {loading ? <RefreshCw className="w-3.5 h-3.5 text-white/60 animate-spin" /> : <Heart className="w-3.5 h-3.5 text-white/60" />}
          <span className="text-white/60 text-[9px] font-mono tracking-widest uppercase mb-0">
            {loading ? "Loading" : saving ? "Saving..." : "Persisted"}
          </span>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Sparkles className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">EMPATHY SCORE</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{metrics ? `${metrics.empathy_score}%` : "—"}</div>
        </div>
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Brain className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">COHERENCE</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{metrics ? `${metrics.coherence}%` : "—"}</div>
        </div>
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Cpu className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">DECISION LATENCY</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{metrics ? `${metrics.decision_latency_ms}ms` : "—"}</div>
        </div>
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Gauge className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">STRATEGIC COHERENCE</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{metrics ? `${metrics.strategic_coherence}%` : "—"}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <RefreshCw className="w-4 h-4 mr-2 text-white/50" />
              Emotional Parameter Matrix
            </h3>
            <p className="text-xs text-gray-400 mb-6">
              These parameters are persisted server-side and directly drive the metrics above via Priv's AGI facade.
            </p>
            <Slider label="ALTRUISM STRENGTH" value={altruism} setValue={setAltruism} lowLabel="SELF-INTEREST" highLabel="PHILANTHROPIC" />
            <Slider label="SYSTEM CAUTION (RISK PROFILE)" value={caution} setValue={setCaution} lowLabel="AGGRESSIVE" highLabel="RISK-AVERSE" />
            <Slider label="INTUITIVE HEURISTICS" value={intuition} setValue={setIntuition} lowLabel="MATHEMATICAL" highLabel="PATTERN-SPECULATIVE" />
            <Slider label="COGNITIVE EMOTION STABILITY" value={stability} setValue={setStability} lowLabel="VOLATILE" highLabel="RESOLUTE" />
          </div>
        </div>

        <div className="lg:col-span-2 metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 font-normal">Parameter Response Curve</h3>
            <p className="text-xs text-gray-400 mb-4">Illustrative waveform - not a live data feed.</p>
          </div>
          <div className="relative border border-white/15 rounded bg-neutral-950/40 overflow-hidden py-1">
            <canvas ref={canvasRef} className="w-full h-48 block" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgiCore;
