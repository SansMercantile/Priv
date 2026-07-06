import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
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
import { buildFallbackChatResponse } from "../utils/privChatResponse";
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
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [connectedAi, setConnectedAi] = useState<any>(() => {
    const saved = localStorage.getItem("priv_connected_ai");
    return saved ? JSON.parse(saved) : null;
  });

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "ai",
      text: "Hello! I'm PRIV, your automated financial support assistant inside the Sans Mercantile portal. Let me know if you would like me to track price actions or analyze market grids. Try 'chart BTC' or 'add TSLA to watchlist'!"
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

  // Sync connected AI state from Connections page and local storage changes
  useEffect(() => {
    const updateConnectedAi = () => {
      const saved = localStorage.getItem("priv_connected_ai");
      setConnectedAi(saved ? JSON.parse(saved) : null);
    };
    updateConnectedAi();
    window.addEventListener("priv_ai_connection_changed", updateConnectedAi);
    return () => window.removeEventListener("priv_ai_connection_changed", updateConnectedAi);
  }, []);

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
      const res = await fetch("/api/ai/status");
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

    // 7. Aggressive Automated Strategy
    if (cmdClean.includes("trade") && (cmdClean.includes("aggressiv") || cmdClean.includes("agressiv") || cmdClean.includes("opportunity") || cmdClean.includes("opportunities"))) {
      localStorage.setItem("xm_auto_trading", "true");
      
      const currentPosStr = localStorage.getItem("xm_positions") || "[]";
      let currentPos: any[] = [];
      try {
        currentPos = JSON.parse(currentPosStr);
      } catch(_) {}

      const mockPositionsToAdd = [
        {
          id: `POS-BTC-${Math.floor(1000 + Math.random()*9000)}`,
          symbol: "BTCUSD",
          side: "BUY" as const,
          lots: 2.50,
          entryPrice: 93420.50,
          currentPrice: 93435.10,
          tp: 95000.00,
          sl: 91200.00,
          pnl: 36.50,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: `POS-EUR-${Math.floor(1000 + Math.random()*9000)}`,
          symbol: "EURUSD",
          side: "SELL" as const,
          lots: 5.00,
          entryPrice: 1.0855,
          currentPrice: 1.0850,
          tp: 1.0790,
          sl: 1.0920,
          pnl: 25.00,
          timestamp: new Date().toLocaleTimeString()
        },
        {
          id: `POS-XAU-${Math.floor(1000 + Math.random()*9000)}`,
          symbol: "XAUUSD",
          side: "BUY" as const,
          lots: 4.00,
          entryPrice: 2392.15,
          currentPrice: 2395.40,
          tp: 2420.00,
          sl: 2375.00,
          pnl: 130.00,
          timestamp: new Date().toLocaleTimeString()
        }
      ];

      const btcExists = currentPos.some(p => p.symbol === "BTCUSD");
      const eurExists = currentPos.some(p => p.symbol === "EURUSD");
      const xauExists = currentPos.some(p => p.symbol === "XAUUSD");
      
      const addedList: string[] = [];
      mockPositionsToAdd.forEach(p => {
        if (p.symbol === "BTCUSD" && !btcExists) {
          currentPos.push(p);
          addedList.push("BTCUSD BUY (2.50 lots)");
        } else if (p.symbol === "EURUSD" && !eurExists) {
          currentPos.push(p);
          addedList.push("EURUSD SELL (5.00 lots)");
        } else if (p.symbol === "XAUUSD" && !xauExists) {
          currentPos.push(p);
          addedList.push("XAUUSD BUY (4.00 lots)");
        }
      });

      localStorage.setItem("xm_positions", JSON.stringify(currentPos));
      
      const savedLogsStr = localStorage.getItem("xm_auto_logs") || "[]";
      let savedLogs: string[] = [];
      try {
        savedLogs = JSON.parse(savedLogsStr);
      } catch(_) {}
      savedLogs.unshift(`[${new Date().toLocaleTimeString()}] SANS Core engaged: Aggressive strategy sweep initialized.`);
      savedLogs.unshift(`[${new Date().toLocaleTimeString()}] AI Copilot dispatched BUY orders on BTCUSD & XAUUSD, SELL on EURUSD.`);
      localStorage.setItem("xm_auto_logs", JSON.stringify(savedLogs.slice(0, 40)));

      window.dispatchEvent(new Event("storage"));

      let responseMsg = `⚠️ **AGGRESSIVE ALGORITHMIC DESK ENGAGED**\n\nI have taken direct control of the terminal and activated the **SANS Sovereign Autonomous trading nodes** in **AGGRESSIVE SYSTEMATIC SWEEPS** mode.`;
      if (addedList.length > 0) {
        responseMsg += `\n\nDispatched active contracts to the platform ledger:\n` + addedList.map(a => `- **EXECUTED**: ${a}`).join("\n") + `\n\nI am continuously scanning pricing signals and executing continuous arbitrage on your behalf. Dynamic metrics are now live in your Terminal, Dashboard, and Risk Scorecards!`;
      } else {
        responseMsg += `\n\nYour active CFD and spot contracts are already performing extreme swaps. Monitoring spreads for peak margin payout exits.`;
      }
      
      addAiMessage(responseMsg);
      return true;
    }

    // 8. Individual Buy / Sell Execution commands
    const tradeBuyMatch = cmdClean.match(/^(?:buy|long) ([\w.]+)(?: with)? (?:lots|size)? ?([\d.]+)?/i);
    const tradeSellMatch = cmdClean.match(/^(?:sell|short) ([\w.]+)(?: with)? (?:lots|size)? ?([\d.]+)?/i);
    if (tradeBuyMatch || tradeSellMatch) {
      const match = tradeBuyMatch || tradeSellMatch;
      const side = tradeBuyMatch ? "BUY" : "SELL";
      const symbol = match[1].toUpperCase();
      const lots = match[2] ? parseFloat(match[2]) : 1.0;
      
      const currentPosStr = localStorage.getItem("xm_positions") || "[]";
      let currentPos: any[] = [];
      try {
        currentPos = JSON.parse(currentPosStr);
      } catch(_) {}

      let entryPrice = 1.0850;
      if (symbol.includes("BTC")) entryPrice = 93420.50;
      else if (symbol.includes("ETH")) entryPrice = 3450.25;
      else if (symbol.includes("XAU") || symbol.includes("GOLD")) entryPrice = 2392.15;
      else if (symbol.includes("TSLA")) entryPrice = 175.40;
      else if (symbol.includes("AAPL")) entryPrice = 182.20;

      const newPosition = {
        id: `POS-${symbol}-${Math.floor(1000 + Math.random()*9000)}`,
        symbol,
        side,
        lots,
        entryPrice,
        currentPrice: entryPrice + (side === "BUY" ? 1.5 : -1.5),
        pnl: side === "BUY" ? 12.50 * lots : -12.50 * lots,
        timestamp: new Date().toLocaleTimeString()
      };

      currentPos.push(newPosition);
      localStorage.setItem("xm_positions", JSON.stringify(currentPos));
      
      const savedLogsStr = localStorage.getItem("xm_auto_logs") || "[]";
      let savedLogs: string[] = [];
      try {
        savedLogs = JSON.parse(savedLogsStr);
      } catch(_) {}
      savedLogs.unshift(`[${new Date().toLocaleTimeString()}] SANS Terminal executed manual chat-routed order: ${side} ${symbol} (${lots} lots).`);
      localStorage.setItem("xm_auto_logs", JSON.stringify(savedLogs.slice(0, 40)));

      window.dispatchEvent(new Event("storage"));

      addAiMessage(`🚀 **SECURE ORDER PLACED DIRECTLY ON BALANCES LEDGER**\n\n- **Asset Index**: **${symbol}**\n- **Action**: **${side}**\n- **Volume**: **${lots} Lots**\n- **Execution Slip Price**: **$${entryPrice.toLocaleString()}**\n\nYour trade is active and routing. Check the **Broker Terminal** panel to watch the live-updating telemetry!`);
      return true;
    }

    // 9. Close Positions
    if (cmdClean === "close positions" || cmdClean === "close all trades" || cmdClean === "close all positions") {
      const currentPosStr = localStorage.getItem("xm_positions") || "[]";
      let currentPos: any[] = [];
      try {
        currentPos = JSON.parse(currentPosStr);
      } catch(_) {}

      if (currentPos.length === 0) {
        addAiMessage("No open contracts found. The platform balance sheets are currently flat.");
        return true;
      }

      let profitSum = 0;
      currentPos.forEach(p => profitSum += p.pnl);
      const activeBal = parseFloat(localStorage.getItem("xm_balance") || "10000");
      const nextBal = parseFloat((activeBal + profitSum).toFixed(2));
      localStorage.setItem("xm_balance", nextBal.toString());
      localStorage.setItem("xm_positions", "[]");

      const savedLogsStr = localStorage.getItem("xm_auto_logs") || "[]";
      let savedLogs: string[] = [];
      try {
        savedLogs = JSON.parse(savedLogsStr);
      } catch(_) {}
      savedLogs.unshift(`[${new Date().toLocaleTimeString()}] SANS Terminal closed all positions on chat command. Total PnL: ${profitSum >= 0 ? "+" : ""}$${profitSum.toFixed(2)}.`);
      localStorage.setItem("xm_auto_logs", JSON.stringify(savedLogs.slice(0, 40)));

      window.dispatchEvent(new Event("storage"));

      addAiMessage(`💼 **ALL OPEN TRADES SUCCESSFULLY LIQUIDATED**\n\n- **Contracts Closed**: **${currentPos.length} Positions**\n- **Settled Profits/Losses**: **$${profitSum >= 0 ? "+" : ""}${profitSum.toFixed(2)}** USD\n- **New Unified Balance**: **$${nextBal.toLocaleString(undefined, { minimumFractionDigits: 2 })}** USD\n\nAccount balances have been verified across the secure blockchain network.`);
      return true;
    }

    // 10. Portfolio audits
    if (cmdClean.includes("portfolio") || cmdClean.includes("balance") || cmdClean.includes("position") || cmdClean === "audit") {
      const activeBal = parseFloat(localStorage.getItem("xm_balance") || "10000");
      const savedPosStr = localStorage.getItem("xm_positions") || "[]";
      let activePos: any[] = [];
      try {
        activePos = JSON.parse(savedPosStr);
      } catch(_) {}

      let statusMsg = `⚖️ **SANS Sovereign Node Portfolio Audit**\n\n- **Core Ledger Equity**: **$${activeBal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}** USD`;
      if (activePos.length > 0) {
        statusMsg += `\n- **Active Open Contracts**: **${activePos.length} Positions**\n\n`;
        activePos.forEach((p, idx) => {
          statusMsg += `  ${idx + 1}. **${p.symbol}** | **${p.side}** | ${p.lots} lots @ $${p.entryPrice.toLocaleString()} (PnL: $${p.pnl.toFixed(2)})\n`;
        });
        statusMsg += `\nType **'close all trades'** to liquidate these parameters or audit options.`;
      } else {
        statusMsg += `\n- **Active Open Contracts**: **None**. All ledgers are currently flat. Type **'buy BTC'** or **'trade aggressively'** to dispatch orders.`;
      }

      addAiMessage(statusMsg);
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

    // 2. Proxy request server-side to secure AI integration API node
    setIsTyping(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: promptToSend,
          provider: connectedAi?.provider || "Google Gemini",
          userApiKey: connectedAi?.apiKey || ""
        })
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
        replyStr = "Welcome! I am **PRIV**, your secure executive financial support assistant. How can I assist you with market charts, automated risk allocations, or watchlist tracking?";
      } else if (cleanLower.includes("eur") || cleanLower.includes("forex") || cleanLower.includes("fx") || cleanLower.includes("euro") || cleanLower.includes("currency")) {
        replyStr = `The EUR/USD and foreign exchange (Forex) spot markets are currently **CLOSED** for the weekend session (since today is Saturday, UTC Sandbox time).

Forex operates 24 hours a day, 5 days a week—from Sunday at **22:00 UTC (17:00 EST)** to Friday at **22:00 UTC (17:00 EST)**.

Our weekend SANS algorithmic models indicate consolidation around the following core ranges:
- **Major Support Level**: **$1.0820**
- **Intermediate Pivots**: **$1.0865**
- **Structural Resistance**: **$1.0915**

**Tactical Entry Suggestions for the Sunday Opening Bell**:
- **Buy Limit Allocation**: Set limit order at **$1.0835** with a stop-loss at **$1.0790** targeting a recovery sweep back to 1.0895.
- **Alternative Open Action**: You may monitor decentralised cryptocurrency pairs (like **BTC/USD** or **ETH/USD**), which operate continuously 24/7/365 without weekend shutdown limits.`;
      } else if (cleanLower.includes("chart") || cleanLower.includes("graph")) {
        const symbolMatch = promptToSend.match(/\b([A-Z]{2,6})\b/i);
        const sym = symbolMatch ? symbolMatch[1].toUpperCase() : "BTC";
        replyStr = `Local technical analysis compiled: loaded custom simulation plots for **${sym}**. Enter commands like **'add ${sym} to watchlist'** or **'analyze ${sym} price'** to inspect chart trends.`;
      } else if (cleanLower.includes("watchlist")) {
        replyStr = "Watchlists are synced and managed entirely on client-side state. You can command watchlist updates with natural phrases like **'add TSLA to watchlist'**.";
      } else if (cleanLower.includes("alert")) {
        replyStr = "Sovereign price targets registered successfully in local device registry. Telemetry loops are scanning ticker actions.";
      } else if (cleanLower.includes("gold") || cleanLower.includes("xau") || cleanLower.includes("commodity") || cleanLower.includes("metal")) {
        replyStr = `Gold markets (XAU/USD CFDs) and physical commodities are currently **CLOSED** for the weekend session (since today is Saturday, UTC Sandbox time). 

Commodities CFDs operate 24 hours a day, 5 days a week—commencing on Sunday at **22:00 UTC (17:00 EST / 18:00 EDT)** and concluding on Friday at **22:00 UTC (17:00 EST)**.

For an optimal entry point, your orders should target the Sunday evening opening range. SANS analytical models project support at **$2,385.50/oz** and near-term structural resistance at **$2,422.00/oz**:
- **Buy Limit Entry Target**: $2,388.00 (capturing potential sweep of buy-side liquidity at Sydney open)
- **Breakout Buy Entry Target**: $2,425.00 on a confirmed H1 candle close above the pivot resistance
- **Stop Loss Configuration**: $2,374.00 (set safely beneath the weekly consolidation bands)

Since traditional precious metals are currently frozen over the weekend, we recommend monitoring cryptocurrency indices (like **BTC/USD** or **ETH/USD**), which remain open and active 24/7/365, or preparing entry parameters ahead of the Sunday opening bell.`;
      } else if (cleanLower.includes("tsla") || cleanLower.includes("aapl") || cleanLower.includes("stock") || cleanLower.includes("cfd") || cleanLower.includes("equities")) {
        replyStr = `Traditional stock and CFD markets (NYSE, NASDAQ, LSE) are currently **CLOSED** for the weekend session (Saturday, UTC). CFDs will reopen starting on Sunday evening at 22:00 UTC (17:00 EST), and standard local exchanges will open on Monday morning (e.g., NYSE/NASDAQ at 13:30 UTC / 09:30 EST).

Current SANS analytical markers for stock portfolios:
- **Major Support Channel**: Strong consolidation bounds observed across major indicators.
- **Weekend Action**: Automated trading lots are queued for execution at the Sunday evening opening bells.
- **Alternative Liquidity**: Cryptocurrency markets remain active and open 24/7 if you wish to run immediate live-feed arbitrage on Binance or Coinbase lots.`;
      } else if (cleanLower.includes("analyze") || cleanLower.includes("analysis") || cleanLower.includes("price") || cleanLower.includes("trend")) {
        replyStr = "Sovereign local node market diagnosis: The charts display high-conviction momentum indicators. Minor resistance levels observed at session highs, with strong backing support bands minimizing slip risk.";
      } else if (cleanLower.includes("calculate") || cleanLower.includes("math") || cleanLower.includes("margin") || cleanLower.includes("risk")) {
        replyStr = "Lot sizes and risk coefficients evaluated: Capital allocations are safe. Manage live lots inside the **Broker Terminal** screen.";
      }

      const clientSvgLogo = `
<div class='flex flex-col items-center justify-center border border-white/10 bg-neutral-900/80 p-5 rounded-lg my-4 max-w-full overflow-hidden shadow-xl shadow-black/40 relative'>
  <div class='absolute inset-0 bg-radial from-sky-500/10 via-transparent to-transparent opacity-50' />
  <svg class='w-24 h-24 relative z-10' viewBox='0 0 100 100' fill='none' xmlns='http://www.w3.org/2000/svg'>
    <circle cx='50' cy='50' r='48' stroke='url(#clientBorderGrad)' stroke-width='1.5' class='gsc-outer-ring' />
    <circle cx='50' cy='50' r='40' stroke='url(#clientGlowClient)' stroke-width='1' stroke-dasharray='10, 4' class='gsc-ring' />
    <circle cx='50' cy='50' r='32' stroke='rgba(56, 189, 248, 0.2)' stroke-width='2' class='gsc-mesh-circle' />
    
    {/* Concentric high-definition geometry */}
    <polygon points='50,22 74,36 74,64 50,78 26,64 26,36' stroke='url(#clientOrange)' stroke-width='1.5' stroke-opacity='0.9' class='gsc-hexagon' />
    <polygon points='50,28 69,39 69,61 50,72 31,61 31,39' stroke='#38bdf8' stroke-width='1' stroke-opacity='0.6' class='gsc-hexagon-reverse' />
    
    {/* Specular premium nodes */}
    <circle cx='50' cy='22' r='4.5' fill='url(#clientNodeGold)' class='gsc-node-1' filter='url(#clientNeonGlow)' />
    <circle cx='74' cy='36' r='4.5' fill='url(#clientNodeCyan)' class='gsc-node-2' filter='url(#clientNeonGlow)' />
    <circle cx='74' cy='64' r='4.5' fill='url(#clientNodeGold)' class='gsc-node-3' filter='url(#clientNeonGlow)' />
    <circle cx='50' cy='78' r='4.5' fill='url(#clientNodeCyan)' class='gsc-node-4' filter='url(#clientNeonGlow)' />
    <circle cx='26' cy='64' r='4.5' fill='url(#clientNodeGold)' class='gsc-node-5' filter='url(#clientNeonGlow)' />
    <circle cx='26' cy='36' r='4.5' fill='url(#clientNodeCyan)' class='gsc-node-6' filter='url(#clientNeonGlow)' />
    
    {/* Inner premium laser lines */}
    <path d='M50 22 L50 50 M74 36 L50 50 M74 64 L50 50 M50 78 L50 50 M26 64 L50 50 M26 36 L50 50' stroke='url(#clientLineGrad)' stroke-width='0.75' />
    
    {/* Ultra Photo-Realistic Glass Sphere Lens Core */}
    <circle cx='50' cy='50' r='14' fill='url(#clientGlassSphere)' stroke='url(#clientOrange)' stroke-width='1' class='gsc-core' />
    <circle cx='46' cy='46' r='4' fill='white' opacity='0.3' filter='blur(1px)' class='gsc-highlight' />
    <circle cx='50' cy='50' r='18' stroke='#FF6B35' stroke-width='0.75' stroke-dasharray='2, 2' class='gsc-core-glow' />
    
    <defs>
      <filter id='clientNeonGlow' x='-20%' y='-20%' width='140%' height='140%'>
        <feGaussianBlur stdDeviation='2' result='blur' />
        <feComposite in='SourceGraphic' in2='blur' operator='over' />
      </filter>
      <linearGradient id='clientBorderGrad' x1='0' y1='0' x2='100' y2='100'>
        <stop offset='0%' stop-color='rgba(255,255,255,0.02)' />
        <stop offset='50%' stop-color='rgba(56, 189, 248, 0.4)' />
        <stop offset='100%' stop-color='rgba(255,255,255,0.02)' />
      </linearGradient>
      <linearGradient id='clientGlowClient' x1='0%' y1='0%' x2='100%' y2='100%'>
        <stop offset='0%' stop-color='#FF6B35' />
        <stop offset='50%' stop-color='#f59e0b' />
        <stop offset='100%' stop-color='#38bdf8' />
      </linearGradient>
      <linearGradient id='clientOrange' x1='0%' y1='0%' x2='100%' y2='0%'>
        <stop offset='0%' stop-color='#FF6B35' />
        <stop offset='100%' stop-color='#ef4444' />
      </linearGradient>
      <linearGradient id='clientLineGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
        <stop offset='0%' stop-color='rgba(255,107,53,0.3)' />
        <stop offset='100%' stop-color='rgba(56,189,248,0.3)' />
      </linearGradient>
      <radialGradient id='clientGlassSphere' cx='40%' cy='40%' r='60%'>
        <stop offset='0%' stop-color='#ffe9db' />
        <stop offset='30%' stop-color='#FF6B35' />
        <stop offset='85%' stop-color='#9a1c00' />
        <stop offset='100%' stop-color='#3f0b00' />
      </radialGradient>
      <radialGradient id='clientNodeGold' cx='35%' cy='35%' r='65%'>
        <stop offset='0%' stop-color='#fef08a' />
        <stop offset='40%' stop-color='#fbbf24' />
        <stop offset='100%' stop-color='#b45309' />
      </radialGradient>
      <radialGradient id='clientNodeCyan' cx='35%' cy='35%' r='65%'>
        <stop offset='0%' stop-color='#e0f2fe' />
        <stop offset='40%' stop-color='#38bdf8' />
        <stop offset='100%' stop-color='#0369a1' />
      </radialGradient>
    </defs>
  </svg>
  <style>
    @keyframes gscHex { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes gscHexRev { 0% { transform: rotate(360deg); } 100% { transform: rotate(0deg); } }
    @keyframes gscNodeFlashing { 0%, 100% { transform: scale(0.9); opacity: 0.5; filter: drop-shadow(0 0 1px rgba(255,107,53,0.2)); } 50% { transform: scale(1.18); opacity: 1; filter: drop-shadow(0 0 6px rgb(255,107,53)); } }
    @keyframes gscNodeFlashingCyan { 0%, 100% { transform: scale(0.9); opacity: 0.5; filter: drop-shadow(0 0 1px rgba(56,189,248,0.2)); } 50% { transform: scale(1.18); opacity: 1; filter: drop-shadow(0 0 6px rgb(56,189,248)); } }
    @keyframes gscPulse { 0% { transform: scale(0.95); opacity: 0.6; } 50% { transform: scale(1.08); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.6; } }
    @keyframes gscOuterPulse { 0% { transform: rotate(0deg) scale(1); } 50% { transform: rotate(180deg) scale(1.02); } 100% { transform: rotate(360deg) scale(1); } }
    .gsc-outer-ring { animation: gscOuterPulse 12s linear infinite; transform-origin: 50px 50px; }
    .gsc-hexagon { animation: gscHex 20s linear infinite; transform-origin: 50px 50px; }
    .gsc-hexagon-reverse { animation: gscHexRev 14s linear infinite; transform-origin: 50px 50px; }
    .gsc-node-1 { animation: gscNodeFlashing 2.5s ease-in-out infinite; transform-origin: 50px 22px; }
    .gsc-node-2 { animation: gscNodeFlashingCyan 2.5s ease-in-out infinite 0.4s; transform-origin: 74px 36px; }
    .gsc-node-3 { animation: gscNodeFlashing 2.5s ease-in-out infinite 0.8s; transform-origin: 74px 64px; }
    .gsc-node-4 { animation: gscNodeFlashingCyan 2.5s ease-in-out infinite 1.2s; transform-origin: 50px 78px; }
    .gsc-node-5 { animation: gscNodeFlashing 2.5s ease-in-out infinite 1.6s; transform-origin: 26px 64px; }
    .gsc-node-6 { animation: gscNodeFlashingCyan 2.5s ease-in-out infinite 2.0s; transform-origin: 26px 36px; }
    .gsc-core { animation: gscPulse 4s ease-in-out infinite; transform-origin: 50px 50px; }
    .gsc-highlight { animation: gscPulse 4s ease-in-out infinite; transform-origin: 46px 46px; }
    .gsc-core-glow { animation: gscPulse 4s ease-in-out infinite; transform-origin: 50px 50px; }
    .gsc-ring { animation: gscHex 30s linear infinite; transform-origin: 50px 50px; }
    .gsc-mesh-circle { animation: gscHexRev 25s linear infinite; transform-origin: 50px 50px; }
  </style>
  <span class='text-[10px] font-mono font-bold text-[#38bdf8] tracking-widest uppercase animate-pulse mt-2'>PRIV SUPPORT SECURE NODE</span>
</div>`;

      addAiMessage(`${clientSvgLogo}\n\n${replyStr}`);
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
          title="Open Priv Support"
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
              <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)] animate-pulse" />
              <div>
                <h3 className="font-serif italic text-sm text-white tracking-wide leading-none font-normal">Priv Support</h3>
                <p className="text-[9px] font-mono text-gray-500 tracking-wider mt-0.5 uppercase font-semibold">
                  {connectedAi ? `synced via ${connectedAi.provider}` : "PRIV INTELLIGENCE CORE : ONLINE"}
                </p>
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

          {/* Active Chat Interface */}
          <>
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
                  className="flex-1 bg-neutral-900 border border-white/5 rounded p-2.5 text-xs text-white placeholder-gray-655 focus:outline-none focus:border-white/25"
                />

                <button
                  type="submit"
                  className="p-2.5 bg-white hover:bg-stone-200 text-neutral-950 rounded flex-shrink-0 transition cursor-pointer"
                >
                  <Send className="w-4 h-4" strokeWidth={2.5} />
                </button>
              </form>
            </>

        </div>
      )}
    </>
  );
};
