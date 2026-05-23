import React, { useState, useEffect } from "react";
import { 
  Landmark, 
  TrendingUp, 
  HelpCircle, 
  CheckCircle, 
  DollarSign, 
  AlertTriangle,
  Play,
  RotateCw,
  Sliders,
  Award,
  BookOpen
} from "lucide-react";

export const TaxIntelligence: React.FC = () => {
  const [revenue, setRevenue] = useState(14.7);
  const [gaps, setGaps] = useState(12843);
  
  // Simulated Simulation Outcomes details
  const [activeSimulation, setActiveSimulation] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [simLogs, setSimLogs] = useState<string[]>([]);

  // Simulation parameters
  const [taxRate, setTaxRate] = useState(28); // South Africa Corporate Tax 27% to 28%
  const [miningRoyalty, setMiningRoyalty] = useState(5.5);

  useEffect(() => {
    const timer = setInterval(() => {
      // Periodic fluctuations
      setRevenue(r => r + (Math.random() - 0.5) * 0.12);
      setGaps(g => g + Math.floor((Math.random() * 8) - 4));
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  const triggerSimulation = (policyType: string) => {
    setSimulating(true);
    setActiveSimulation(policyType);
    setSimLogs(["Deploying CPPN Evolver algorithms...", "Contacting GRA & SARS sovereign boundary databases..."]);

    setTimeout(() => {
      setSimLogs(prev => [...prev, "Ingesting local mining output yields...", "Parsing transfer pricing spreads..."]);
    }, 1000);

    setTimeout(() => {
      let outcome = "";
      if (policyType === "corporate") {
        const yieldDiff = (taxRate - 27) * 0.42;
        outcome = `SIMULATION COMPLETE: CORPORATE TAX POLICY SHIFT
Base rate: ${taxRate}% (Shift from 27% base)
Sovereign Sentiment Stance: Moderate (84.2%)
Predicted Fiscal Yield Impact: ${yieldDiff > 0 ? "+" : ""}${yieldDiff.toFixed(2)} Billion ZAR / GHS
Compliance Gap Index: Reduced by 1.2% due to neuro-symbolic anti-evasion matching.`;
      } else if (policyType === "mining") {
        const royaltyYield = (miningRoyalty - 5) * 0.12;
        outcome = `SIMULATION COMPLETE: EXTRACTIVE MINING PENALTIES
Ad-valorem Royalty Rate: ${miningRoyalty}% (Shift from 5.0% base)
Local Community Sentiment: Bullish (91.4%)
Expected Mineral Export Revenue Delta: ${royaltyYield > 0 ? "+" : ""}${royaltyYield.toFixed(2)} Billion ZAR
Multinational Slippage Risk: Low-to-Moderate. Anti-shifting filters stabilized.`;
      } else {
        outcome = `SIMULATION COMPLETE: CITIZEN ENGAGEMENT FILING SCHEMAS
Introduction of sovereign instant-filing interfaces.
Compliance Index Projection: Shifts to 98.4% (+3.2% rise)
Auditing Resource Latency: Retracted by 420 hrs / mo.
SARS compliance declarations automated successfully.`;
      }

      setSimLogs(prev => [...prev, outcome]);
      setSimulating(false);
    }, 2800);
  };

  return (
    <div className="space-y-6">
      {/* Head */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white font-normal">Tax Intelligence Engine</h1>
          <p className="text-white/40 text-xs mt-1 font-light font-sans">Sovereign revenue forecasting and automated compliance bridging for governments (SARS & GRA)</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs">
          <Landmark className="w-3.5 h-3.5 text-white/50" />
          <span className="text-white/60 font-medium font-sans uppercase">Gov-Tech Services Active</span>
        </div>
      </div>

      {/* Stats Cards displays */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <DollarSign className="text-white/60 w-4 h-4" />
            <h4 className="text-[9px] font-mono text-gray-400 tracking-wider">PREDICTED SOVEREIGN REVENUE</h4>
          </div>
          <div className="text-3xl font-light text-white">${revenue.toFixed(2)}B</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">YIELD ESTIMATION: OPTIMAL</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <AlertTriangle className="text-white/60 w-4 h-4" />
            <h4 className="text-[9px] font-mono text-gray-400 tracking-wider">IDENTIFIED COMPLIANCE GAPS</h4>
          </div>
          <div className="text-3xl font-light text-white">{gaps.toLocaleString()}</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">Bridging: active</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <Award className="text-white/60 w-4 h-4" />
            <h4 className="text-[9px] font-mono text-gray-400 tracking-wider">SIMULATION STABILITY ACCURACY</h4>
          </div>
          <div className="text-3xl font-light text-white">97.3%</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">MODEL COUPLING: RESOLUTE</div>
        </div>

        <div className="metric-card rounded p-5 border-white/10">
          <div className="flex items-center space-x-3 mb-2">
            <TrendingUp className="text-white/60 w-4 h-4" />
            <h4 className="text-[9px] font-mono text-gray-400 tracking-wider">CITIZEN TRUST COEFFICIENT</h4>
          </div>
          <div className="text-3xl font-light text-white">88.9%</div>
          <div className="text-[9px] font-mono text-white/40 mt-1 uppercase">Cognitive compliance metrics</div>
        </div>

      </div>

      {/* Main interactive grid splitting columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Simulators and outcomes parameters */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Policy simulator sandbox */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <BookOpen className="w-4 h-4 mr-2 text-white/55" />
              Sovereign Policy Sandbox Simulators
            </h3>
            <p className="text-xs text-stone-400 mb-6 font-sans leading-relaxed">
              Model regulatory taxation outcomes prior to e-filing. Simulating corporate bracket margins and resource royalty margins under alternative pricing schemas.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Corporate bracket */}
              <div className="p-4 bg-neutral-900/40 border border-white/5 rounded space-y-4">
                <h4 className="text-[10px] font-mono text-stone-400 uppercase tracking-widest">corporate bracket adjustment</h4>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono text-gray-300">
                    <span>Base Corp Tax Rate</span>
                    <span className="text-white font-bold">{taxRate}%</span>
                  </div>
                  <input 
                    type="range"
                    min="20"
                    max="40"
                    step="1"
                    value={taxRate}
                    onChange={(e) => setTaxRate(Number(e.target.value))}
                    className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                    <span>20% (LOW)</span>
                    <span>40% (HIGH)</span>
                  </div>
                </div>

                <div className="pt-2">
                  <button 
                    onClick={() => triggerSimulation("corporate")}
                    disabled={simulating}
                    className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-medium text-xs p-2.5 rounded transition duration-200 flex items-center justify-center space-x-1 border border-white cursor-pointer"
                  >
                    <Play className="w-3 h-3 fill-neutral-950 text-neutral-950 inline" />
                    <span>{simulating && activeSimulation === "corporate" ? "MODELING BRACKETS..." : "RUN BRACKET SIMULATION"}</span>
                  </button>
                </div>
              </div>

              {/* Mining royalty */}
              <div className="p-4 bg-neutral-900/40 border border-white/5 rounded space-y-4">
                <h4 className="text-[10px] font-mono text-stone-400 uppercase tracking-widest">Mineral Extraction royalty</h4>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono text-gray-300">
                    <span>Export Royalty Rate</span>
                    <span className="text-white font-bold">{miningRoyalty}%</span>
                  </div>
                  <input 
                    type="range"
                    min="2"
                    max="10"
                    step="0.5"
                    value={miningRoyalty}
                    onChange={(e) => setMiningRoyalty(Number(e.target.value))}
                    className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                    <span>2.0% (EXPORT INC)</span>
                    <span>10.0% (HIGH YIELD)</span>
                  </div>
                </div>

                <div className="pt-2">
                  <button 
                    onClick={() => triggerSimulation("mining")}
                    disabled={simulating}
                    className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-medium text-xs p-2.5 rounded transition duration-200 flex items-center justify-center space-x-1 border border-white cursor-pointer"
                  >
                    <Play className="w-3 h-3 fill-neutral-950 text-neutral-950 inline" />
                    <span>{simulating && activeSimulation === "mining" ? "PREDICTING ROYALTIES..." : "RUN MINERAL SIMULATION"}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Results logs */}
        <div className="metric-card rounded p-6 flex flex-col justify-between border-white/10">
          <div>
            <h3 className="text-base font-serif italic text-white mb-4 font-normal">
              Simulation Sandbox Results
            </h3>
            <p className="text-xs text-stone-400 mb-4 font-sans leading-relaxed">
              Consensus simulation outcomes generated by the CPPN neural evolver and SARS transfer-pricing audit scripts.
            </p>
          </div>

          <div className="p-3 bg-neutral-950 border border-white/5 rounded flex-1 min-h-[180px] text-xs font-mono text-gray-400 space-y-2 overflow-y-auto">
            {simLogs.length === 0 ? (
              <div className="text-gray-650 italic">Clear. Initiate a policy simulation parameters slider to inspect sovereign outcomes in real-time.</div>
            ) : (
              simLogs.map((log, idx) => (
                <div key={idx} className={`${idx === simLogs.length - 1 && log.startsWith("SIMULATION") ? "text-white/90 border border-white/10 p-2.5 rounded bg-white/5 leading-relaxed" : "text-gray-400 font-light"}`}>
                  {log}
                </div>
              ))
            )}
          </div>

          <div className="border-t border-white/10 mt-5 pt-4 text-[11px] font-mono text-gray-500 flex justify-between">
            <span>GOV CONNECTOR STATS:</span>
            <span className="text-white/60 font-medium font-sans uppercase">Secure (100%)</span>
          </div>
        </div>

      </div>
    </div>
  );
};
