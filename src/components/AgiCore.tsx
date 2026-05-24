import React, { useState, useEffect, useRef } from "react";
import { Brain, Sparkles, Heart, RefreshCw, Cpu, Gauge } from "lucide-react";

export const AgiCore: React.FC<{ demoMode?: boolean }> = () => {
  const [altruism, setAltruism] = useState(84);
  const [caution, setCaution] = useState(72);
  const [intuition, setIntuition] = useState(91);
  const [stability, setStability] = useState(95);

  const [empathyScore, setEmpathyScore] = useState(88.4);
  const [coherence, setCoherence] = useState(94.2);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Recalculate empathy score dynamically when user drags controls
  useEffect(() => {
    const rawEmpathy = (altruism * 0.4 + intuition * 0.3 + (100 - caution) * 0.2 + stability * 0.1);
    setEmpathyScore(parseFloat(rawEmpathy.toFixed(1)));
    
    const rawCoherence = (stability * 0.5 + caution * 0.2 + altruism * 0.3);
    setCoherence(parseFloat(rawCoherence.toFixed(1)));
  }, [altruism, caution, intuition, stability]);

  // Consciousness Cortex Brainwave Canvas Simulator
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
      
      // Draw gridlines
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

      // Draw 3 wave layers correlating to AGI cores
      const waveLayers = [
        { amplitude: 35, freq: 0.008, speed: 0.05, stroke: "rgba(255, 255, 255, 0.4)", width: 2 },
        { amplitude: 20, freq: 0.015, speed: -0.07, stroke: "rgba(163, 163, 163, 0.3)", width: 1.5 },
        { amplitude: 12, freq: 0.025, speed: 0.09, stroke: "rgba(255, 255, 255, 0.15)", width: 1 }
      ];

      waveLayers.forEach((layer) => {
        ctx.beginPath();
        ctx.strokeStyle = layer.stroke;
        ctx.lineWidth = layer.width;
        
        for (let x = 0; x < width; x++) {
          // Compute Y coordinate with simple sine wave sum
          const y = height / 2 + 
            Math.sin(x * layer.freq + phase * layer.speed) * layer.amplitude * (stability / 100) + 
            Math.sin(x * 0.005 + phase * 0.02) * 5;
          
          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      });

      phase += 0.5;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [stability]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white">AGI Core Intelligence</h1>
          <p className="text-white/40 text-xs font-light mt-1">Unified consciousness, emotional tuning and decision alignment nodes</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10">
          <Heart className="w-3.5 h-3.5 text-white/60 animate-pulse" />
          <span className="text-white/60 text-[9px] font-mono tracking-widest uppercase mb-0">Empathy Deployed</span>
        </div>
      </div>

      {/* Primary Analytics cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Sparkles className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">EMPATHY COEFFICIENT</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{empathyScore}%</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">ALIGNMENT: HARMONIZED</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Brain className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">CONSCIOUSNESS CORRELATION</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">{coherence}%</div>
          <div className="text-[9px] font-mono text-emerald-500 mt-1 uppercase">COGNITIVE LEVEL: META-STABLE</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Cpu className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">DECISION LATENCY</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">0.002s</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">INTEGRATOR: NEURO-SYMBOLIC</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Gauge className="text-white/65 w-4 h-4" />
            <h4 className="text-xs font-mono text-gray-400 tracking-wider">STRATEGIC COHERENCE</h4>
          </div>
          <div className="text-2xl font-light text-white font-mono">99.98%</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">TOLERANCE RATIO: OPTIMAL</div>
        </div>
      </div>

      {/* Main interactive grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tuning board */}
        <div className="metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <RefreshCw className="w-4 h-4 mr-2 text-white/50 animate-spin" />
              Emotional Parameter Matrix
            </h3>
            <p className="text-xs text-gray-400 mb-6">
              Adjust PRIV Core's ethical orientation. Slide variables to alter decision priorities on the flies.
            </p>
            
            {/* Altruism */}
            <div className="space-y-2 mb-5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">ALTRUISM STRENGTH</span>
                <span className="text-white font-bold font-mono">{altruism}%</span>
              </div>
              <input 
                type="range"
                value={altruism}
                onChange={(e) => setAltruism(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>SELF-INTEREST</span>
                <span>PHILANTHROPIC</span>
              </div>
            </div>

            {/* Caution */}
            <div className="space-y-2 mb-5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">SYSTEM CAUTION (RISK PROFILE)</span>
                <span className="text-white font-bold font-mono">{caution}%</span>
              </div>
              <input 
                type="range"
                value={caution}
                onChange={(e) => setCaution(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>AGGRESSIVE</span>
                <span>RISK-AVERSE</span>
              </div>
            </div>

            {/* Intuition */}
            <div className="space-y-2 mb-5">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">INTUITIVE HEURISTICS</span>
                <span className="text-white font-semibold font-mono">{intuition}%</span>
              </div>
              <input 
                type="range"
                value={intuition}
                onChange={(e) => setIntuition(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>MATHEMATICAL</span>
                <span>PATTERN-SPECULATIVE</span>
              </div>
            </div>

            {/* Stability */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">COGNITIVE EMOTION STABILITY</span>
                <span className="text-white font-semibold font-mono">{stability}%</span>
              </div>
              <input 
                type="range"
                value={stability}
                onChange={(e) => setStability(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>VOLATILE</span>
                <span>RESOLUTE</span>
              </div>
            </div>
          </div>

          <div className="border-t border-white/5 mt-6 pt-4 text-[9px] font-mono text-white/30 uppercase">
            Parameters stabilized by symbolic cradle node.
          </div>
        </div>

        {/* Brainwave visualizer */}
        <div className="lg:col-span-2 metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 font-normal">
              Real-time Cortical Wave Cortex
            </h3>
            <p className="text-xs text-gray-400 mb-4">
              Visualizing synthetic consciousness pathways and cognitive coherence feedback across our micro-VM arrays.
            </p>
          </div>

          <div className="relative border border-white/15 rounded bg-neutral-950/40 overflow-hidden py-1">
            <canvas ref={canvasRef} className="w-full h-48 block" />
            <div className="absolute top-2 right-2 flex items-center space-x-1 font-mono text-[9px] text-white/50 px-2 py-0.5 bg-white/5 rounded border border-white/10">
              <span className="w-1 h-1 bg-white/60 rounded-full animate-bounce" />
              <span>LOGIC STATE: QUANTUM COUPLING</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-4 border-t border-white/10">
            <div>
              <h5 className="text-xs font-bold text-white mb-1">Ethical Guardrails Active</h5>
              <p className="text-[11px] text-gray-400 leading-snug">
                The empathy cradle engine verifies strategic investments against 14 constitutional compliance indices.
              </p>
            </div>
            <div>
              <h5 className="text-xs font-bold text-white mb-1">Decentralized Arbitration</h5>
              <p className="text-[11px] text-gray-400 leading-snug">
                Subatomic consensus avoids computational local minima, assuring ethical execution speed and low latency.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgiCore;
