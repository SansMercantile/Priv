import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Database, 
  Wifi, 
  Cpu, 
  PlusCircle, 
  Sliders, 
  Play, 
  CheckCircle,
  Network
} from "lucide-react";
import { DataFeed, DataHistoryPoint } from "../types";

export const DataIngestion: React.FC<{ demoMode?: boolean }> = () => {
  const [ingestionRate, setIngestionRate] = useState(1); // multiplier
  const [feeds, setFeeds] = useState<DataFeed[]>([
    {
      id: 1,
      name: "Binance WebSocket Delta",
      type: "Orderbook L1/L2 feeds",
      status: "active",
      throughput: 1420,
      latency: 0.001,
      iconName: "Wifi",
      color: "green",
      description: "Direct cryptocurrency exchange spreads and volume details."
    },
    {
      id: 2,
      name: "Federal Reserve RSS Node",
      type: "Policy and Statement Scraping",
      status: "active",
      throughput: 42,
      latency: 0.024,
      iconName: "Database",
      color: "blue",
      description: "Monetary policy statement text feed and rate metrics."
    },
    {
      id: 3,
      name: "SARS SA Tax Gateway",
      type: "Revenue Registry Records",
      status: "active",
      throughput: 112,
      latency: 0.042,
      iconName: "Network",
      color: "purple",
      description: "South African Revenue Service e-filing clearance portal sync."
    },
    {
      id: 4,
      name: "West African Shipping AIS satellite",
      type: "Alternative Supply Manifests",
      status: "monitoring",
      throughput: 8,
      latency: 1.250,
      iconName: "Activity",
      color: "yellow",
      description: "Satellite tracking vessel drafts and crude freight departures."
    }
  ]);

  const [history, setHistory] = useState<DataHistoryPoint[]>([]);

  // Input state for adding custom data feeds
  const [newFeedName, setNewFeedName] = useState("");
  const [newFeedType, setNewFeedType] = useState("Rest API");
  const [newFeedDesc, setNewFeedDesc] = useState("");
  const [banner, setBanner] = useState("");

  useEffect(() => {
    // Generate base timeline
    const baseHistory = Array.from({ length: 8 }, (_, i) => ({
      id: i,
      source: feeds[Math.floor(Math.random() * feeds.length)].name,
      volume: Math.floor(Math.random() * 40 * ingestionRate) + 5,
      timestamp: Date.now() - i * 3000,
      type: ["price", "news", "sentiment", "order"][Math.floor(Math.random() * 4)] as any
    }));
    setHistory(baseHistory);

    const timer = setInterval(() => {
      // Dynamic updates
      setFeeds(prev => 
        prev.map(f => ({
          ...f,
          throughput: Math.floor(f.throughput + (Math.random() - 0.5) * 20 * ingestionRate),
          latency: Math.max(0.001, parseFloat((f.latency + (Math.random() - 0.5) * 0.005).toFixed(3)))
        }))
      );

      // Scroll recent points
      const randomFeed = feeds[Math.floor(Math.random() * feeds.length)];
      setHistory(prev => [
        {
          id: Date.now(),
          source: randomFeed.name,
          volume: Math.floor(Math.random() * 50 * ingestionRate) + 10,
          timestamp: Date.now(),
          type: ["price", "news", "sentiment", "order"][Math.floor(Math.random() * 4)] as any
        },
        ...prev.slice(0, 11)
      ]);
    }, 3000);

    return () => clearInterval(timer);
  }, [ingestionRate, feeds]);

  const createCustomFeed = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFeedName.trim()) return;

    const nextFeed: DataFeed = {
      id: feeds.length + 1,
      name: newFeedName,
      type: newFeedType,
      status: "active",
      throughput: 200,
      latency: 0.015,
      iconName: "Database",
      color: "blue",
      description: newFeedDesc || "Custom configured user input intelligence feed."
    };

    setFeeds(prev => [...prev, nextFeed]);
    setBanner(`Successfully deployed Data Gateway: ${newFeedName}!`);
    setNewFeedName("");
    setNewFeedDesc("");
    setTimeout(() => setBanner(""), 4000);
  };

  const getStatusStyle = (status: string) => {
    if (status === "active") return "bg-white/5 text-white/80 border border-white/10";
    if (status === "monitoring") return "bg-white/5 text-white/50 border border-white/5";
    return "bg-white/5 text-white/40 border border-white/5";
  };

  return (
    <div className="space-y-6">
      {/* Overview Head */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white">Data Ingestion Framework</h1>
          <p className="text-white/40 text-xs mt-1 font-light">Ingesting high-density trading inputs, news feeds, and public policy variables</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10">
          <Wifi className="w-3.5 h-3.5 text-white/60" />
          <span className="text-white/60 text-[9px] font-mono tracking-widest uppercase mb-0">INGESTION SPEED: {(ingestionRate * 100).toFixed(0)}%</span>
        </div>
      </div>

      {banner && (
        <div className="bg-white/5 border border-white/15 text-white/90 px-4 py-3 rounded text-sm flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-white/70" />
          <span>{banner}</span>
        </div>
      )}

      {/* Main Grid: Lists and additions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Source listing (left colspan: 2) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Database className="w-4 h-4 mr-2 text-white/50" />
              Connected Data Gantry Ports
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {feeds.map(feed => (
                <div key={feed.id} className="p-4 bg-neutral-900/20 border border-white/5 rounded flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-sm font-medium text-white">{feed.name}</h4>
                      <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded-full ${getStatusStyle(feed.status)}`}>
                        {feed.status}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 font-mono mb-2 uppercase">{feed.type}</p>
                    <p className="text-xs text-gray-400 font-sans mb-4 leading-relaxed">{feed.description}</p>
                  </div>
                  
                  <div className="flex justify-between items-center border-t border-white/5 pt-3 font-mono text-[9px]">
                    <div>
                      <span className="text-gray-500 uppercase mr-1">THROUGHPUT:</span>
                      <span className="text-white font-medium">{(feed.throughput * ingestionRate).toFixed(0)} bps</span>
                    </div>
                    <div>
                      <span className="text-gray-500 uppercase mr-1">LATENCY:</span>
                      <span className="text-white/60">{(feed.latency / ingestionRate).toFixed(3)}s</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline chart/list of incoming packets */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Network className="w-4 h-4 mr-2 text-white/50" />
              Decentralized Feed Stream Inlets
            </h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {history.map((pt, idx) => (
                <div key={idx} className="p-3 bg-neutral-950/40 border border-white/5 rounded font-mono text-center">
                  <div className="text-[9px] text-white/30 uppercase truncate mb-1">{pt.source}</div>
                  <div className="text-xs font-bold text-white/80">+{pt.volume} pts</div>
                  <div className="text-[8px] text-white/40 mt-1 uppercase font-semibold">[{pt.type}]</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bandwidth and addition controllers */}
        <div className="space-y-6">
          
          {/* Ingestion speed slider */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <Sliders className="w-4 h-4 mr-2 text-white/50" />
              Ingestion Bandwidth Throttle
            </h3>
            <p className="text-xs text-stone-400 mb-6 font-sans">
              Increase multiplier rate to simulate premium institutional fiber links or satellite pipeline feeds.
            </p>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-gray-300">MULTIPLIER EFFECT</span>
                <span className="text-white font-bold">{ingestionRate}x (TURBO)</span>
              </div>
              <input 
                type="range"
                min="1"
                max="5"
                step="1"
                value={ingestionRate}
                onChange={(e) => setIngestionRate(Number(e.target.value))}
                className="w-full accent-white bg-neutral-900 rounded appearance-none h-1 cursor-pointer"
              />
              <div className="flex justify-between text-[9px] text-gray-500 font-mono">
                <span>1x STANDARD REST</span>
                <span>5x SATELLITE GIGAPORT</span>
              </div>
            </div>
          </div>

          {/* New feed creation */}
          <div className="metric-card rounded p-6 border-white/10">
            <h3 className="text-base font-serif italic text-white mb-4 flex items-center font-normal">
              <PlusCircle className="w-4 h-4 mr-2 text-white/50" />
              Deploy Custom Gateway
            </h3>
            
            <form onSubmit={createCustomFeed} className="space-y-4">
              <div>
                <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-wider mb-1">Gateway Name</label>
                <input 
                  type="text" 
                  value={newFeedName} 
                  onChange={(e) => setNewFeedName(e.target.value)}
                  placeholder="e.g., SARS margin payout gate"
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-white/30"
                  required
                />
              </div>

               <div>
                <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-wider mb-1">Gateway Inlet Protocol</label>
                <select 
                  value={newFeedType} 
                  onChange={(e) => setNewFeedType(e.target.value)}
                  className="w-full bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white focus:outline-none focus:border-white/30"
                >
                  <option value="Rest API">REST API Endpoint</option>
                  <option value="Websocket">Secure WebSocket L2</option>
                  <option value="AIS Satellite link">AIS Satellite Link</option>
                  <option value="gRPC Streams">gRPC Multiplex Stream</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-mono text-gray-500 uppercase tracking-wider mb-1">Inlet Description</label>
                <textarea 
                  value={newFeedDesc} 
                  onChange={(e) => setNewFeedDesc(e.target.value)}
                  placeholder="Simulated details..."
                  className="w-full h-16 bg-neutral-900 border border-white/10 rounded p-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-white/30 resize-none font-sans"
                />
              </div>

              <div className="pt-2">
                <button 
                  type="submit" 
                  className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-medium text-xs p-3 rounded transition duration-200 flex items-center justify-center space-x-1 border border-white cursor-pointer"
                >
                  <Play className="w-3 h-3 block fill-neutral-950 text-neutral-950" />
                  <span>INITIALIZE PORT GATE</span>
                </button>
              </div>
            </form>
          </div>

        </div>

      </div>
    </div>
  );
};

export default DataIngestion;
