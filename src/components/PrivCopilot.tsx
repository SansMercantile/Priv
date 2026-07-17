import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare, X, Send, Mic, Volume2, VolumeX, Brain, RefreshCw, TrendingUp, TrendingDown, Calendar,
} from "lucide-react";
import chatAvatar from "../assets/images/chat_avatar_1779278082106.png";

interface HarmonicPoint {
  index: number;
  price: number;
}
interface HarmonicPattern {
  name: string;
  direction: string;
  points: { X: HarmonicPoint; A: HarmonicPoint; B: HarmonicPoint; C: HarmonicPoint; D: HarmonicPoint };
}
interface TradingSignal {
  direction: string;
  signal_strength: number;
  entry: number;
  stop_loss: number;
  take_profit_1: number;
  take_profit_2: number;
  take_profit_3: number;
  basis: string;
}
interface EconomicEvent {
  title?: string;
  event?: string;
  date?: string;
  impact?: string;
  currency?: string;
}
interface SupportResponse {
  message: string;
  symbol?: string;
  technical_analysis?: {
    recommendation?: { recommendation: string; aggression: string } | null;
    harmonic_patterns?: HarmonicPattern[];
    fuzzy_signal_strength?: number;
  };
  fundamentals?: {
    economic_calendar_events?: EconomicEvent[];
    economic_calendar_link?: string;
  };
  trading_signal?: TradingSignal | null;
  position_advice?: Array<{ order_id: string; symbol: string; note: string }>;
}

interface ChatMessage {
  sender: "user" | "ai";
  text?: string;
  data?: SupportResponse;
}

// Real pattern/signal chart - plots the detected harmonic X-A-B-C-D points
// and the entry/stop-loss/take-profit levels. No fabricated price series.
const PatternSignalChart: React.FC<{ pattern?: HarmonicPattern; signal?: TradingSignal | null }> = ({ pattern, signal }) => {
  if (!pattern && !signal) return null;
  const w = 300;
  const h = 160;
  const padding = 24;

  const allPrices: number[] = [];
  if (pattern) Object.values(pattern.points).forEach((p) => allPrices.push(p.price));
  if (signal) allPrices.push(signal.entry, signal.stop_loss, signal.take_profit_1, signal.take_profit_2, signal.take_profit_3);
  if (allPrices.length === 0) return null;

  const minP = Math.min(...allPrices);
  const maxP = Math.max(...allPrices);
  const range = maxP - minP || 1;
  const getY = (price: number) => h - padding - ((price - minP) / range) * (h - 2 * padding);

  const pointOrder: Array<keyof HarmonicPattern["points"]> = ["X", "A", "B", "C", "D"];
  const xPositions = pointOrder.map((_, i) => padding + (i / 4) * (w - 2 * padding));

  return (
    <div className="mt-3 p-3 bg-neutral-950 border border-white/10 rounded">
      <h4 className="font-sans text-[10px] text-white/70 mb-2 font-medium tracking-wide">
        {pattern ? `${pattern.name} PATTERN` : "SIGNAL LEVELS"}
      </h4>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto">
        {pattern && (
          <>
            <polyline
              points={pointOrder.map((key, i) => `${xPositions[i]},${getY(pattern.points[key].price)}`).join(" ")}
              fill="none"
              stroke="rgba(255,255,255,0.6)"
              strokeWidth="1.5"
            />
            {pointOrder.map((key, i) => (
              <g key={key}>
                <circle cx={xPositions[i]} cy={getY(pattern.points[key].price)} r="3" fill="#fff" />
                <text x={xPositions[i]} y={getY(pattern.points[key].price) - 8} fill="#aaa" fontSize="9" textAnchor="middle" fontFamily="monospace">
                  {key}
                </text>
              </g>
            ))}
          </>
        )}
        {signal && (
          <>
            <line x1={padding} y1={getY(signal.entry)} x2={w - padding} y2={getY(signal.entry)} stroke="#60a5fa" strokeWidth="1" strokeDasharray="3,2" />
            <line x1={padding} y1={getY(signal.stop_loss)} x2={w - padding} y2={getY(signal.stop_loss)} stroke="#f87171" strokeWidth="1" strokeDasharray="3,2" />
            <line x1={padding} y1={getY(signal.take_profit_1)} x2={w - padding} y2={getY(signal.take_profit_1)} stroke="#34d399" strokeWidth="1" strokeDasharray="2,2" opacity="0.6" />
            <line x1={padding} y1={getY(signal.take_profit_2)} x2={w - padding} y2={getY(signal.take_profit_2)} stroke="#34d399" strokeWidth="1" strokeDasharray="2,2" opacity="0.8" />
            <line x1={padding} y1={getY(signal.take_profit_3)} x2={w - padding} y2={getY(signal.take_profit_3)} stroke="#34d399" strokeWidth="1" strokeDasharray="2,2" />
          </>
        )}
      </svg>
      {signal && (
        <div className="mt-2 grid grid-cols-2 gap-1.5 text-[9px] font-mono">
          <div className="text-blue-400">Entry: {signal.entry}</div>
          <div className="text-red-400">SL: {signal.stop_loss}</div>
          <div className="text-emerald-400">TP1: {signal.take_profit_1}</div>
          <div className="text-emerald-400">TP2: {signal.take_profit_2}</div>
          <div className="text-emerald-400">TP3: {signal.take_profit_3}</div>
          <div className="text-zinc-500">{signal.direction}</div>
        </div>
      )}
    </div>
  );
};

const SignalCard: React.FC<{ data: SupportResponse }> = ({ data }) => {
  const rec = data.technical_analysis?.recommendation;
  const pattern = data.technical_analysis?.harmonic_patterns?.slice(-1)[0];
  const events = data.fundamentals?.economic_calendar_events || [];

  return (
    <div className="mt-2 space-y-2">
      {rec && (
        <div className="flex items-center gap-2 text-[10px] font-mono">
          {rec.recommendation === "BUY" ? (
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          ) : rec.recommendation === "SELL" ? (
            <TrendingDown className="w-3.5 h-3.5 text-red-400" />
          ) : null}
          <span className="text-white font-bold">{rec.recommendation}</span>
          <span className="text-zinc-500">({rec.aggression})</span>
        </div>
      )}
      <PatternSignalChart pattern={pattern} signal={data.trading_signal} />
      {events.length > 0 && (
        <div className="p-2 bg-neutral-950 border border-white/5 rounded">
          <div className="flex items-center gap-1.5 text-[9px] text-zinc-500 font-mono uppercase mb-1">
            <Calendar className="w-3 h-3" /> Upcoming Economic Events
          </div>
          {events.slice(0, 3).map((ev, i) => (
            <div key={i} className="text-[9px] font-mono text-zinc-400">
              {ev.currency ? `[${ev.currency}] ` : ""}{ev.title || ev.event || "Event"}
            </div>
          ))}
          <a href={data.fundamentals?.economic_calendar_link} className="text-[9px] font-mono text-blue-400 underline">
            View full calendar
          </a>
        </div>
      )}
      {data.position_advice && data.position_advice.length > 0 && (
        <div className="p-2 bg-amber-500/5 border border-amber-500/20 rounded text-[9px] font-mono text-amber-400">
          {data.position_advice[0].note}
        </div>
      )}
    </div>
  );
};

export const PrivCopilot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "ai",
      text: "Hello, I'm Priv. Ask me about a symbol (e.g. \"analyze R_100\" or \"EURUSD\") and I'll pull real technical analysis, detected chart patterns, and a trading signal with entry, stop loss, and three take-profit levels.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [speechActive, setSpeechActive] = useState(true);
  const [micActive, setMicActive] = useState(false);

  const messageEndRef = useRef<HTMLDivElement | null>(null);
  const speechRecognizer = useRef<any>(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognitionAPI) {
      const recognizer = new SpeechRecognitionAPI();
      recognizer.continuous = false;
      recognizer.interimResults = false;
      recognizer.lang = "en-US";
      recognizer.onresult = (e: any) => {
        const transcript = e.results[0][0].transcript;
        if (transcript) setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
      };
      recognizer.onend = () => setMicActive(false);
      speechRecognizer.current = recognizer;
    }
  }, []);

  const toggleMicrophone = () => {
    if (!speechRecognizer.current) {
      alert("Microphone recognition is not supported in this browser.");
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

  const speak = (text: string) => {
    if (!speechActive || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const promptToSend = input.trim();
    if (!promptToSend) return;

    setMessages((prev) => [...prev, { sender: "user", text: promptToSend }]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch("/api/v1/support/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: promptToSend }),
      });
      const data: SupportResponse = await res.json();
      if (res.ok) {
        setMessages((prev) => [...prev, { sender: "ai", text: data.message, data }]);
        speak(data.message);
      } else {
        const errText = (data as any).detail || "Priv's analysis engine is temporarily unavailable.";
        setMessages((prev) => [...prev, { sender: "ai", text: errText }]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { sender: "ai", text: `I couldn't reach the analysis engine: ${err.message || err}. Please try again shortly.` },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full p-0.5 bg-black border border-white/20 hover:scale-105 transition-all duration-300 flex items-center justify-center cursor-pointer"
          title="Open Priv Support"
        >
          <div className="w-full h-full rounded-full overflow-hidden relative">
            <img alt="Priv" className="w-full h-full object-cover rounded-full" src={chatAvatar} referrerPolicy="no-referrer" />
          </div>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-0 right-0 sm:bottom-6 sm:right-6 w-full h-full sm:w-[430px] sm:h-[82vh] sm:max-h-[750px] bg-neutral-950/95 backdrop-blur-2xl rounded-none sm:rounded-lg z-50 flex flex-col overflow-hidden border border-white/10 shadow-2xl">
          <header className="flex items-center justify-between p-4 border-b border-white/10 flex-shrink-0 bg-neutral-950">
            <div className="flex items-center space-x-2.5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div>
                <h3 className="font-serif italic text-sm text-white font-normal">Priv Support</h3>
                <p className="text-[9px] font-mono text-gray-500 tracking-wider mt-0.5 uppercase font-semibold">
                  Real technical + fundamental analysis
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setSpeechActive(!speechActive)}
                className={`p-1.5 rounded border transition ${speechActive ? "text-white border-white/25 bg-white/5" : "text-gray-500 border-white/5"}`}
              >
                {speechActive ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
              </button>
              <button onClick={() => setIsOpen(false)} className="p-1 rounded-full hover:bg-white/5 text-gray-400 hover:text-white transition">
                <X className="w-4 h-4" />
              </button>
            </div>
          </header>

          <div className="flex-1 p-4 overflow-y-auto scrollbar-hide space-y-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex items-start gap-2.5 ${msg.sender === "user" ? "justify-end" : ""}`}>
                {msg.sender === "ai" && (
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/15 flex items-center justify-center flex-shrink-0 mt-1">
                    <Brain className="w-3 h-3 text-white/50" />
                  </div>
                )}
                <div
                  className={`max-w-[88%] p-3 rounded text-xs whitespace-pre-wrap leading-relaxed border ${
                    msg.sender === "user" ? "bg-white/5 border-white/15 text-white" : "bg-neutral-900 border-white/5 text-gray-200"
                  }`}
                >
                  {msg.text && <p>{msg.text}</p>}
                  {msg.data && <SignalCard data={msg.data} />}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex items-center gap-2 text-stone-500 text-[10px] font-mono pl-8">
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>Analyzing real market data...</span>
              </div>
            )}
            <div ref={messageEndRef} />
          </div>

          <form onSubmit={handleSendMessage} className="p-3 border-t border-white/10 bg-neutral-950 flex-shrink-0 flex items-center space-x-2">
            <button
              type="button"
              onClick={toggleMicrophone}
              className={`p-2.5 rounded border transition flex-shrink-0 ${
                micActive ? "text-white border-white/20 bg-white/10 animate-pulse" : "text-gray-500 border-white/5 hover:text-white hover:bg-white/5"
              }`}
            >
              <Mic className="w-4 h-4" />
            </button>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. 'analyze EURUSD' or 'chart R_100'..."
              className="flex-1 bg-neutral-900 border border-white/5 rounded p-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-white/25"
            />
            <button type="submit" className="p-2.5 bg-white hover:bg-stone-200 text-neutral-950 rounded flex-shrink-0 transition">
              <Send className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </form>
        </div>
      )}
    </>
  );
};
