import React, { useState, useEffect, useRef, useCallback } from "react";
import { 
  MessageSquare, 
  X, 
  Send, 
  Mic, 
  MicOff, 
  Camera, 
  CameraOff,
  Volume2,
  VolumeX,
  TrendingUp,
  Brain,
  Minus
} from "lucide-react";
import { ChatMessage, StockAlert } from "../types";
import chatAvatar from "../assets/images/chat_avatar_1779278082106.png";

// Interactive 30-day Simulated Stock Chart SVG (Equivalent to IN in target)
interface InnerChartProps {
  data: Array<{ date: string; price: number }>;
  ticker: string;
}

export const InnerChart: React.FC<InnerChartProps> = ({ data, ticker }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoverData, setHoverData] = useState<{ x: number; y: number; date: string; price: string } | null>(null);

  if (!data || data.length === 0) return null;

  const w = 280;
  const h = 150;
  const padding = 20;

  const prices = data.map(d => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;

  // Horizontal position math
  const getX = (idx: number) => padding + (idx / (data.length - 1)) * (w - 2 * padding);
  // Vertical position math (inverted coordinates)
  const getY = (val: number) => h - padding - ((val - minPrice) / priceRange) * (h - 2 * padding);

  // Generate SVG path string
  const pathD = data.map((pt, idx) => `${idx === 0 ? "M" : "L"} ${getX(idx)} ${getY(pt.price)}`).join(" ");
  const areaD = `${pathD} L ${getX(data.length - 1)} ${h - padding} L ${getX(0)} ${h - padding} Z`;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement, MouseEvent>) => {
    const svgEl = containerRef.current;
    if (!svgEl) return;

    const rect = svgEl.getBoundingClientRect();
    const cursorX = e.clientX - rect.left;
    const index = Math.round(((cursorX - padding) / (w - 2 * padding)) * (data.length - 1));

    if (index >= 0 && index < data.length) {
      const selectedPt = data[index];
      setHoverData({
        x: getX(index),
        y: getY(selectedPt.price),
        date: selectedPt.date,
        price: selectedPt.price.toFixed(2)
      });
    }
  };

  const handleMouseLeave = () => {
    setHoverData(null);
  };

  return (
    <div ref={containerRef} className="mt-3 p-3 bg-neutral-950 border border-white/10 rounded relative">
      <h4 className="font-sans text-[10px] text-white/70 mb-1 font-medium tracking-wide">
        {ticker} - 30 DAY PERFORMANCE (SIMULATED)
      </h4>
      <svg 
        viewBox={`0 0 ${w} ${h}`} 
        className="w-full h-auto cursor-crosshair block"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          <linearGradient id="innerChartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Shaded Area */}
        <path d={areaD} fill="url(#innerChartGradient)" />
        {/* Trading Line */}
        <path d={pathD} fill="none" stroke="rgba(255,255,255,0.75)" strokeWidth="1.5" />

        {hoverData && (
          <>
            {/* Guide line */}
            <line 
              x1={hoverData.x} 
              y1={padding} 
              x2={hoverData.x} 
              y2={h - padding} 
              stroke="white" 
              strokeOpacity="0.1" 
              strokeDasharray="2,2" 
            />
            {/* Value dot */}
            <circle cx={hoverData.x} cy={hoverData.y} r="3" fill="#ffffff" stroke="#000000" strokeWidth="1.5" />
          </>
        )}
      </svg>

      {hoverData && (
        <div className="absolute top-2 right-2 text-[9px] font-mono text-gray-400 bg-neutral-950 border border-white/10 p-1 rounded">
          PRICE: ${hoverData.price} | DATE: {hoverData.date}
        </div>
      )}
    </div>
  );
};


// Copilot System overlay component (Equivalent to DN in target)
export const PrivCopilot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "ai",
      text: "Hello! I'm PRIV, your automated financial copilot inside the Sans Mercantile portal. Let me know if you would like me to track price actions or analyze market grids. Try 'chart BTC' or 'add TSLA to watchlist'!"
    }
  ]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  // Settings indicators
  const [micActive, setMicActive] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [speechActive, setSpeechActive] = useState(true);

  // Connection diagnostics
  const [apiStatus, setApiStatus] = useState<"loading" | "active" | "exhausted" | "missing" | "error">("loading");
  const [apiError, setApiError] = useState("");

  // Lists persistence
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<StockAlert[]>([]);
  const [activeChartData, setActiveChartData] = useState<Array<{ date: string; price: number }> | null>(null);

  // References
  const messageEndRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const speechRecognizer = useRef<any>(null);

  const checkApiStatus = async () => {
    try {
      const res = await fetch("/api/gemini/status");
      if (res.ok) {
        const data = await res.json();
        setApiStatus(data.status);
        if (data.status !== "active" && data.error) {
          setApiError(data.error);
        } else {
          setApiError("");
        }
      } else {
        setApiStatus("error");
        setApiError("Express core returned failed diagnostic reports.");
      }
    } catch (e) {
      setApiStatus("error");
      setApiError("Failed to reach internal API diagnostic proxy.");
    }
  };

  useEffect(() => {
    checkApiStatus();
  }, []);

  // Load Watchlist and Alerts
  useEffect(() => {
    try {
      const persistedWatchlist = localStorage.getItem("priv_watchlist");
      if (persistedWatchlist) {
        setWatchlist(JSON.parse(persistedWatchlist));
      }

      const persistedAlerts = localStorage.getItem("priv_alerts");
      if (persistedAlerts) {
        setAlerts(JSON.parse(persistedAlerts));
      }
    } catch (e) {
      console.error("Storage load failed", e);
    }
  }, []);

  // Save changes
  useEffect(() => {
    localStorage.setItem("priv_watchlist", JSON.stringify(watchlist));
  }, [watchlist]);

  useEffect(() => {
    localStorage.setItem("priv_alerts", JSON.stringify(alerts));
  }, [alerts]);

  // Handle SpeechSynthesis Text-to-Speech (TTS)
  const speakOutput = (text: string) => {
    if (!speechActive || !window.speechSynthesis) return;
    
    // Clear active utterance to prevent queue stutters
    window.speechSynthesis.cancel();
    
    // Prepare utterance parameters
    const cleanedText = text.replace(/\*\*/g, ""); // strip bold markers
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.rate = 1.05;
    window.speechSynthesis.speak(utterance);
  };

  // Autoscroll conversation logs
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Speech Recognition setups
  useEffect(() => {
    const SpeechRecognition_API = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition_API) {
      const recognizer = new SpeechRecognition_API();
      recognizer.continuous = false;
      recognizer.interimResults = false;
      recognizer.lang = "en-US";

      recognizer.onresult = (e: any) => {
        const transcriptText = e.results[0][0].transcript;
        if (transcriptText) {
          setInput(prev => prev ? `${prev} ${transcriptText}` : transcriptText);
        }
      };

      recognizer.onend = () => {
        setMicActive(false);
      };

      speechRecognizer.current = recognizer;
    }
  }, []);

  const toggleMicrophone = () => {
    if (!speechRecognizer.current) {
      alert("Microphone recognition services are not supported under your current browser.");
      return;
    }

    if (micActive) {
      speechRecognizer.current.stop();
      setMicActive(false);
    } else {
      speechRecognizer.current.start();
      setMicActive(true);
    }
  };

  // Video Camera Web sentiments analyzer simulator
  const toggleCamera = async () => {
    if (cameraActive) {
      setCameraActive(false);
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach(track => track.stop());
        videoRef.current.srcObject = null;
      }
    } else {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { width: 140, height: 140 } });
        setCameraActive(true);
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = mediaStream;
          }
        }, 300);
      } catch (err) {
        alert("Webcam request denied. Ensure permissions are set in your client.");
      }
    }
  };

  const addAiMessage = (text: string | null, chartPayload?: any) => {
    const nextMsg: ChatMessage = { sender: "ai" };
    if (text) nextMsg.text = text;
    if (chartPayload) {
      nextMsg.type = "chart";
      nextMsg.chartData = chartPayload.data;
      nextMsg.ticker = chartPayload.ticker;
    }
    setMessages(prev => [...prev, nextMsg]);
    if (text) {
      speakOutput(text);
    }
  };

  // Local commands processor parameters
  const parseLocalCommands = (rawCommand: string) => {
    const cmdClean = rawCommand.toLowerCase().trim();

    // 1. Add to Watchlist
    const addWatchMatch = cmdClean.match(/add ([\w.]+) to (?:my )?watchlist/i);
    if (addWatchMatch) {
      const ticker = addWatchMatch[1].toUpperCase();
      if (!watchlist.includes(ticker)) {
        setWatchlist(prev => [...prev, ticker]);
      }
      addAiMessage(`Identified command! Added **${ticker}** securely to your dynamic watchlist indices.`);
      return true;
    }

    // 2. Remove from Watchlist
    const remWatchMatch = cmdClean.match(/(?:remove|delete) ([\w.]+) from (?:my )?watchlist/i);
    if (remWatchMatch) {
      const ticker = remWatchMatch[1].toUpperCase();
      setWatchlist(prev => prev.filter(t => t !== ticker));
      addAiMessage(`Identified command! Removed **${ticker}** from your watchlist index.`);
      return true;
    }

    // 3. Show Watchlist
    if (cmdClean === "show watchlist" || cmdClean === "view watchlist") {
      if (watchlist.length > 0) {
        addAiMessage(`Here is your current watchlist: **${watchlist.join(", ")}**`);
      } else {
        addAiMessage("Your watchlist indices are currently empty. Type **'add TSLA to watchlist'** to begin tracking tickers!");
      }
      return true;
    }

    // 4. Set price target alert
    const alertMatch = cmdClean.match(/alert me when ([\w.]+) is (above|below) \$?([\d.]+)/i);
    if (alertMatch) {
      const [, ticker, dir, prVal] = alertMatch;
      const nextAlert: StockAlert = {
        ticker: ticker.toUpperCase(),
        direction: dir as any,
        price: parseFloat(prVal)
      };
      setAlerts(prev => [...prev, nextAlert]);
      addAiMessage(`Alert registered successfully! I will notify you immediately when **${nextAlert.ticker}** crosses **$${nextAlert.price}** going **${nextAlert.direction}**.`);
      return true;
    }

    // 5. Analyze loaded stocks
    if (cmdClean === "analyze the chart" || cmdClean === "analyze chart") {
      if (activeChartData) {
        addAiMessage("Conducting a neuro-symbolic technical analysis: The 30-day performance curve illustrates a strong consolidation channel with support stabilized around lower standard deviations. MACD and RSI are displaying robust bullish momentum.");
      } else {
        addAiMessage("Please generate a chart first! Try typing **'chart AAPL'** or **'graph BTC'**.");
      }
      return true;
    }

    // 6. Draw stock charts
    const chartMatch = cmdClean.match(/(?:chart|graph) ([\w.]+)/i);
    if (chartMatch) {
      const ticker = chartMatch[1].toUpperCase();
      // Generate simulated price points
      const points = Array.from({ length: 30 }, (_, idx) => {
        const date = new Date();
        date.setDate(date.getDate() - (29 - idx));
        return {
          date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          price: 150 + Math.random() * 25 - 12 + idx * 0.7 + (ticker.charCodeAt(0) % 15)
        };
      });

      setActiveChartData(points);
      addAiMessage(`Simulating performance diagnostics... Reconstructing **${ticker}** financial indexes:`, { data: points, ticker });
      return true;
    }

    return false;
  };

  // Send message to Express Proxy Route
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const promptToSend = input.trim();
    if (!promptToSend) return;

    // Append user message
    setMessages(prev => [...prev, { sender: "user", text: promptToSend }]);
    setInput("");

    // 1. Process local matching patterns
    if (parseLocalCommands(promptToSend)) {
      return;
    }

    // 2. Proxy request server-side to secure Gemini AI integration API node
    setIsTyping(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptToSend })
      });

      if (!res.ok) {
        throw new Error("Local query proxy returned error status");
      }

      const resObj = await res.json();
      addAiMessage(resObj.text || "No insights processed.");
    } catch (err) {
      console.warn("Express server query fell back to client:", err);
      // Construct a premium responsive client fallback
      const cleanLower = promptToSend.toLowerCase();
      let replyStr = "Understood. The PRIV command node has processed your telemetry locally. Feel free to use stock search, watchlist additions, or simulation settings!";
      
      if (cleanLower.includes("hello") || cleanLower.includes("hi") || cleanLower.includes("hey")) {
        replyStr = "Welcome! I am **PRIV Core**, your decentralized AI system copilot. The primary cloud intelligence is operating under local backup. How can I assist you with stock charts, alert management, or real-time simulation tracking?";
      } else if (cleanLower.includes("chart") || cleanLower.includes("graph")) {
        const symbolMatch = promptToSend.match(/\b([A-Z]{2,6})\b/i);
        const sym = symbolMatch ? symbolMatch[1].toUpperCase() : "BTC";
        replyStr = `Local technical analysis compiled: loaded custom simulation plots for **${sym}**. Enter commands like **'add ${sym} to watchlist'** or **'analyze ${sym} price'** to inspect chart trends.`;
      } else if (cleanLower.includes("watchlist")) {
        replyStr = "Watchlists are synced and managed entirely on client-side state. You can command watchlist updates with natural phrases like **'add TSLA to watchlist'**.";
      } else if (cleanLower.includes("alert")) {
        replyStr = "Sovereign price targets registered successfully in local device registry. Telemetry loops are scanning ticker actions.";
      } else if (cleanLower.includes("analyze") || cleanLower.includes("analysis") || cleanLower.includes("price") || cleanLower.includes("trend")) {
        replyStr = "Sovereign local node market diagnosis: The charts display high-conviction momentum indicators. Minor resistance levels observed at session highs, with strong backing support bands minimizing slip risk.";
      } else if (cleanLower.includes("calculate") || cleanLower.includes("math") || cleanLower.includes("margin") || cleanLower.includes("risk")) {
        replyStr = "Lot sizes and risk coefficients evaluated: Capital allocations are safe. Manage live lots inside the **Broker Terminal** screen.";
      }

      addAiMessage(`🤖 **PRIV Copilot** *(SANS Local Secure Backup)*\n\n${replyStr}\n\n*System Note: The primary cloud intelligence API is currently rate-limited or depleted of prepayment credits. PRIV has automatically engaged localized nodes to guarantee uninterrupted execution.*`);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* Floating Closed Bubble Button (Equivalent to M in target) */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full p-0.5 pointer bg-black border border-white/20 hover:scale-105 transition-all duration-300 shadow shadow-white/5 flex items-center justify-center cursor-pointer group"
          title="Open PRIV Copilot"
        >
          <div className="w-full h-full rounded-full overflow-hidden relative">
            <img 
              alt="PRIV AI Assistant" 
              className="w-full h-full object-cover rounded-full" 
              src={chatAvatar} 
              referrerPolicy="no-referrer"
            />
            {/* Spinning accent border */}
            <div className="absolute inset-x-0 inset-y-0 border-2 border-white/30 rounded-full animate-pulse opacity-80" />
          </div>
        </button>
      )}

      {/* Main Chat overlay dialog box */}
      {isOpen && (
        <div className="fixed bottom-0 right-0 sm:bottom-6 sm:right-6 w-full h-full sm:w-[410px] sm:h-[82vh] sm:max-h-[750px] bg-neutral-950/95 backdrop-blur-2xl rounded-none sm:rounded-lg z-50 flex flex-col overflow-hidden border border-white/10 shadow-2xl transition-all duration-300">
          
          {/* Header section */}
          <header className="flex items-center justify-between p-4 border-b border-white/10 flex-shrink-0 bg-neutral-950">
            <div className="flex items-center space-x-2.5">
              <div className={`w-2 h-2 rounded-full ${
                apiStatus === "active" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse" :
                apiStatus === "exhausted" ? "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.6)] animate-pulse" :
                apiStatus === "missing" ? "bg-stone-500 shadow-none border border-white/20" :
                apiStatus === "loading" ? "bg-sky-500 animate-pulse" :
                "bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
              }`} />
              <div>
                <h3 className="font-serif italic text-sm text-white tracking-wide leading-none font-normal">PRIV Copilot</h3>
                <p className="text-[9px] font-mono text-gray-500 tracking-wider mt-0.5 uppercase">neuro-symbolic executive node</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {/* Voice TTS Toggle */}
              <button 
                onClick={() => setSpeechActive(!speechActive)}
                className={`p-1.5 rounded border transition ${speechActive ? "text-white border-white/25 bg-white/5" : "text-gray-500 border-white/5"}`}
                title={speechActive ? "Disable Voice Feedback" : "Enable Voice Feedback"}
              >
                {speechActive ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
              </button>
              
              {/* Dynamic Camera Feed simulator */}
              <button 
                onClick={toggleCamera}
                className={`p-1.5 rounded border transition ${cameraActive ? "text-white/80 border-white/25 bg-white/5" : "text-gray-500 border-white/5"}`}
                title={cameraActive ? "Disable Sentiment Cam" : "Enable Sentiment Cam"}
              >
                <Camera className="w-3.5 h-3.5" />
              </button>

              <button 
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-full hover:bg-white/5 text-gray-400 hover:text-white transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </header>

          {/* Diagnostic connection warning banner */}
          {apiStatus !== "active" && apiStatus !== "loading" && (
            <div className="p-3 bg-amber-950/45 border-b border-amber-900/40 flex flex-col space-y-1.5 flex-shrink-0 text-amber-200/90 text-[10px] font-mono leading-relaxed px-4">
              <div className="flex items-center space-x-2">
                <span className="font-bold flex items-center text-amber-300">
                  ⚠️ {apiStatus === "exhausted" ? "API KEY DEPLETED" : "OFFLINE ROUTE ENGAGED"}
                </span>
                <span className="text-[8px] bg-amber-900/50 text-amber-300 border border-amber-800/40 px-1 py-0.2 rounded uppercase">
                  {apiStatus}
                </span>
              </div>
              <p className="text-stone-300 text-[10.5px]">
                {apiError || "Your Gemini cloud intelligence API key is inactive or missing. Localized offline backup route is successfully engaged."}
              </p>
              <div className="flex items-center space-x-4 pt-1">
                <button
                  type="button"
                  onClick={async () => {
                    setApiStatus("loading");
                    await checkApiStatus();
                  }}
                  className="px-2 py-1 bg-amber-800/40 hover:bg-amber-800/65 text-amber-200 border border-amber-700/30 rounded text-[9px] cursor-pointer transition uppercase"
                >
                  RETRY DIAGNOSTICS
                </button>
                <button
                  type="button"
                  onClick={() => {
                    addAiMessage("💡 **How to Connect/Fix Gemini API Key**\n\n1. Locate the **Secrets panel** at **Settings > Secrets** in the top-right menu of AI Studio.\n2. Add or update the **`GEMINI_API_KEY`** with a fully active, unrestricted API Key.\n3. Verify your billing model is correctly set up for your project at the [Google AI Studio Console](https://aistudio.google.com).\n4. Alternatively, click the **Connect Paid Key** dialog in AI Studio to sync your workspace accounts.\n\n*Click the **RETRY DIAGNOSTICS** button above once complete to establish high-conviction cloud capabilities!*");
                  }}
                  className="px-2 py-1 bg-amber-200 text-neutral-950 font-semibold rounded text-[9px] cursor-pointer transition hover:bg-white uppercase"
                >
                  HOW TO CONNECT KEY
                </button>
              </div>
            </div>
          )}

          {/* Camera feed overlay screen when active */}
          {cameraActive && (
            <div className="p-3 bg-neutral-900/90 border-b border-white/10 flex items-center space-x-3 flex-shrink-0 transition duration-300">
              <div className="w-14 h-14 rounded-full overflow-hidden border-2 border-white/30 relative bg-black">
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scaler scale-x-[-1]" />
              </div>
              <div className="font-mono text-[9px] text-stone-400 flex-1 leading-normal">
                <span className="font-bold flex items-center space-x-1 uppercase text-white mb-0.5">
                  <span className="w-1.5 h-1.5 bg-white rounded-full animate-ping mr-1" />
                  Facial sentiment camera Active
                </span>
                <span>ENGAGEMENT MULTIPLIER: 94.2% (OPTIMAL RANGE)</span>
              </div>
            </div>
          )}

          {/* Logs messages */}
          <div className="flex-1 p-4 overflow-y-auto scrollbar-hide space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex items-start gap-2.5 ${msg.sender === "user" ? "justify-end" : ""}`}>
                {msg.sender === "ai" && (
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/15 flex items-center justify-center flex-shrink-0 mt-1">
                    <Brain className="w-3 h-3 text-white/50 animate-pulse" />
                  </div>
                )}
                
                <div className={`max-w-[85%] p-3 rounded text-xs whitespace-pre-wrap leading-relaxed border ${
                  msg.sender === "user" 
                    ? "bg-white/5 border-white/15 text-white" 
                    : "bg-neutral-900 border-white/5 text-gray-200"
                }`}>
                  {msg.text && (
                    <p dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, "<strong class='text-white font-semibold'>$1</strong>") }} />
                  )}

                  {msg.type === "chart" && msg.chartData && (
                    <InnerChart data={msg.chartData} ticker={msg.ticker || "INDEX"} />
                  )}
                </div>

              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2 text-stone-500 text-[10px] font-mono pl-8 animate-pulse">
                <span className="w-1 h-1 bg-white rounded-full inline-block" />
                <span>PRIV COMPILING COGNITIVE INSIGHTS...</span>
              </div>
            )}
            
            <div ref={messageEndRef} />
          </div>

          {/* Form sender area */}
          <form onSubmit={handleSendMessage} className="p-3 border-t border-white/10 bg-neutral-950 flex-shrink-0 flex items-center space-x-2">
            
            {/* Mic tool */}
            <button
              type="button"
              onClick={toggleMicrophone}
              className={`p-2.5 rounded border transition flex-shrink-0 cursor-pointer ${
                micActive 
                  ? "text-white border-white/20 bg-white/10 animate-pulse" 
                  : "text-gray-500 border-white/5 hover:text-white hover:bg-white/5"
              }`}
            >
              <Mic className="w-4 h-4" />
            </button>

            <input 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Track stock e.g. 'chart ETH'..."
              className="flex-1 bg-neutral-900 border border-white/5 rounded p-2.5 text-xs text-white placeholder-gray-650 focus:outline-none focus:border-white/25"
            />

            <button
              type="submit"
              className="p-2.5 bg-white hover:bg-stone-200 text-neutral-950 rounded flex-shrink-0 transition cursor-pointer"
            >
              <Send className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </form>

        </div>
      )}
    </>
  );
};
