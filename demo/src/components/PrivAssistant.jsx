import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, Mic, Send, Video, X, MessageSquare, BrainCircuit, Volume2, Bell, XCircle, BarChart2 } from 'lucide-react';

// To make the component self-contained, we'll define a simple style injector
const CustomStyles = () => (
  <style>{`
    @keyframes gradient-animation {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    .gradient-text {
      background: linear-gradient(45deg, #34d399, #60a5fa, #a78bfa);
      background-size: 200% 200%;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: gradient-animation 5s ease infinite;
    }
    .glass-morphism {
      background: rgba(25, 35, 50, 0.6);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .scrollbar-hide::-webkit-scrollbar {
      display: none;
    }
    .scrollbar-hide {
      -ms-overflow-style: none;
      scrollbar-width: none;
    }
    @keyframes pulse-glow {
      0%, 100% { box-shadow: 0 0 8px 0px rgba(52, 211, 153, 0.4); }
      50% { box-shadow: 0 0 16px 4px rgba(52, 211, 153, 0.6); }
    }
    .listening-glow {
      animation: pulse-glow 2s infinite ease-in-out;
    }
    .chart-tooltip {
        position: absolute;
        padding: 4px 8px;
        background: rgba(0,0,0,0.7);
        color: white;
        border-radius: 4px;
        font-size: 12px;
        pointer-events: none;
        transform: translate(-50%, -110%);
        opacity: 0;
        transition: opacity 0.2s;
    }
  `}</style>
);

// Self-contained Toast component
const Toast = ({ message, onDismiss }) => {
  if (!message) return null;

  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000);
    return () => clearTimeout(timer);
  }, [message, onDismiss]);

  const bgColor = message.variant === 'destructive' ? 'bg-red-500/80' : 'bg-gray-800/90';

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className={`fixed bottom-4 left-1/2 -translate-x-1/2 p-4 rounded-lg text-white shadow-lg z-[100] ${bgColor} backdrop-blur-sm`}
    >
      <p className="font-bold">{message.title}</p>
      {message.description && <p className="text-sm text-gray-300">{message.description}</p>}
    </motion.div>
  );
};

// Typing indicator component for showing AI is "thinking"
const TypingIndicator = () => (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="flex items-center gap-3"
    >
      <div className="flex-shrink-0">
         <BrainCircuit className="w-6 h-6 text-green-400" />
      </div>
      <div className="flex items-center gap-1.5 p-3 rounded-xl bg-green-500/20">
        <motion.div className="w-2 h-2 bg-green-400 rounded-full" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, repeat: Infinity }} />
        <motion.div className="w-2 h-2 bg-green-400 rounded-full" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, delay: 0.2, repeat: Infinity }} />
        <motion.div className="w-2 h-2 bg-green-400 rounded-full" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, delay: 0.4, repeat: Infinity }} />
      </div>
    </motion.div>
);

// Self-contained SVG Chart component for financial data
const SimpleStockChart = ({ data, ticker }) => {
    const svgRef = useRef(null);
    const [tooltip, setTooltip] = useState(null);

    if (!data || data.length === 0) return null;

    const width = 280;
    const height = 150;
    const padding = 20;

    const prices = data.map(p => p.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    const getX = (index) => padding + (index / (data.length - 1)) * (width - 2 * padding);
    const getY = (price) => height - padding - ((price - minPrice) / (maxPrice - minPrice)) * (height - 2 * padding);

    const path = data.map((point, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(point.price)}`).join(' ');

    const handleMouseMove = (e) => {
        const svg = svgRef.current;
        if (!svg) return;
        const rect = svg.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.round(((x - padding) / (width - 2 * padding)) * (data.length - 1));
        
        if(index >= 0 && index < data.length) {
            const point = data[index];
            setTooltip({
                x: getX(index),
                y: getY(point.price),
                date: point.date,
                price: point.price.toFixed(2),
            });
        }
    };

    const handleMouseLeave = () => setTooltip(null);
    
    return (
        <div className="mt-2">
            <h4 className="font-bold text-sm text-white mb-1">
                {ticker} - 30 Day Performance (Simulated)
            </h4>
            <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} className="w-full h-auto cursor-crosshair">
                <defs>
                    <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#34d399" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
                    </linearGradient>
                </defs>
                <path d={path} fill="none" stroke="#34d399" strokeWidth="2" />
                <path d={`${path} L ${width - padding} ${height - padding} L ${padding} ${height - padding} Z`} fill="url(#chartGradient)" />
                {tooltip && (
                    <>
                        <line x1={tooltip.x} y1={padding} x2={tooltip.x} y2={height - padding} stroke="#a78bfa" strokeWidth="1" strokeDasharray="3,3" />
                        <circle cx={tooltip.x} cy={tooltip.y} r="4" fill="#a78bfa" stroke="white" strokeWidth="2" />
                        <foreignObject x={tooltip.x} y={tooltip.y} width="1" height="1" overflow="visible">
                            <div className="chart-tooltip" style={{ opacity: 1 }}>
                                Price: ${tooltip.price}<br />
                                Date: {tooltip.date}
                            </div>
                        </foreignObject>
                    </>
                )}
            </svg>
        </div>
    );
};


const PrivAssistant = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
      { sender: 'ai', text: "Hello! I'm PRIV, your personal financial AI. How can I assist? Try asking me to chart a stock, then ask me to analyze it." }
  ]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [toast, setToast] = useState(null);
  const [isTtsEnabled, setIsTtsEnabled] = useState(false);
  const [watchlist, setWatchlist] = useState(() => JSON.parse(localStorage.getItem('priv_watchlist')) || []);
  const [alerts, setAlerts] = useState(() => JSON.parse(localStorage.getItem('priv_alerts')) || []);
  const [lastChartData, setLastChartData] = useState(null);


  const videoRef = useRef(null);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    localStorage.setItem('priv_watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  useEffect(() => {
    localStorage.setItem('priv_alerts', JSON.stringify(alerts));
  }, [alerts]);
  
  // Simulate checking alerts every 30 seconds
  useEffect(() => {
    const alertInterval = setInterval(() => {
      if (alerts.length > 0) {
        const randomAlert = alerts[Math.floor(Math.random() * alerts.length)];
        // Simulate a 10% chance of an alert triggering to avoid spam
        if (Math.random() < 0.1) {
            const triggeredPrice = randomAlert.direction === 'above' ? randomAlert.price + 5 : randomAlert.price - 5;
            const alertMessage = {
                sender: 'ai',
                text: `**Proactive Alert:** ${randomAlert.ticker} has moved ${randomAlert.direction} your target of $${randomAlert.price}. Current simulated price is $${triggeredPrice.toFixed(2)}.`
            };
            setMessages(prev => [...prev, alertMessage]);
            // Remove the triggered alert
            setAlerts(prev => prev.filter(a => a.ticker !== randomAlert.ticker));
        }
      }
    }, 30000);
    return () => clearInterval(alertInterval);
  }, [alerts]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if(finalTranscript) setInput(prev => prev + finalTranscript);
      };
      recognitionRef.current = recognition;
    }
  }, []);

  const showToast = (message) => {
    setToast(message);
  };
  
  const speak = (text) => {
    if (!isTtsEnabled || !window.speechSynthesis) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    window.speechSynthesis.speak(utterance);
  };

  const addMessage = (sender, text, data = {}) => {
      const newMessage = { sender, text, ...data };
      setMessages(prev => [...prev, newMessage]);
      if (sender === 'ai' && text) {
          speak(text);
      }
  };

  const callGeminiAPI = async (prompt) => {
    setIsTyping(true);
    const apiKey = "";
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key=${apiKey}`;
    
    const systemPrompt = "You are PRIV, a sophisticated AI financial assistant. Your tone is professional and insightful. Provide concise, data-driven analysis. When handling commands for watchlist, alerts, or charts, confirm the action clearly and succinctly.";

    const payload = {
        contents: [{ parts: [{ text: prompt }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
    };

    try {
        let response;
        let retries = 3;
        let delay = 1000;
        while(retries > 0) {
            response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (response.ok) break;
            retries--;
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2;
        }

        if (!response.ok) throw new Error(`API request failed with status ${response.status}`);
        
        const result = await response.json();
        const text = result.candidates?.[0]?.content?.parts?.[0]?.text;
        
        if (text) {
            addMessage('ai', text);
        } else {
            throw new Error("Invalid response structure from API.");
        }
    } catch (error) {
        console.error("Gemini API call failed:", error);
        addMessage('ai', "I'm having trouble connecting to my core systems. Please try again in a moment.");
    } finally {
        setIsTyping(false);
    }
  };
  
  const generateAnalysisFromData = (chartData) => {
    if (!chartData || chartData.length < 2) return null;

    const startPrice = chartData[0].price;
    const endPrice = chartData[chartData.length - 1].price;
    const prices = chartData.map(p => p.price);
    const highPoint = Math.max(...prices);
    const lowPoint = Math.min(...prices);
    const trend = endPrice > startPrice ? 'upward' : 'downward';
    const changePercentage = (((endPrice - startPrice) / startPrice) * 100).toFixed(2);

    let volatility = 0;
    for (let i = 1; i < prices.length; i++) {
        volatility += Math.abs(prices[i] - prices[i-1]);
    }
    const avgVolatility = (volatility / prices.length).toFixed(2);
    
    // Create a summary string of key data points for the AI to analyze
    return `The stock shows a general ${trend} trend over the last 30 days, with a ${changePercentage}% change. It reached a high of $${highPoint.toFixed(2)} and a low of $${lowPoint.toFixed(2)}. The average daily price fluctuation was around $${avgVolatility}, suggesting moderate volatility.`;
  };

  const handleLocalCommands = (text) => {
    const upperText = text.toUpperCase();
    let match;

    // Add to watchlist
    match = text.match(/add ([\w.]+) to (?:my )?watchlist/i);
    if(match) {
        const ticker = match[1].toUpperCase();
        if(!watchlist.includes(ticker)) {
            setWatchlist(prev => [...prev, ticker]);
        }
        addMessage('ai', `Added ${ticker} to your watchlist.`);
        return true;
    }
    
    // Remove from watchlist
    match = text.match(/(?:remove|delete) ([\w.]+) from (?:my )?watchlist/i);
    if (match) {
        const ticker = match[1].toUpperCase();
        setWatchlist(prev => prev.filter(t => t !== ticker));
        addMessage('ai', `Removed ${ticker} from your watchlist.`);
        return true;
    }

    // Show watchlist
    if (text.match(/show (?:my )?watchlist/i)) {
        if (watchlist.length > 0) {
            addMessage('ai', `Here is your current watchlist: ${watchlist.join(', ')}`);
        } else {
            addMessage('ai', "Your watchlist is currently empty.");
        }
        return true;
    }
    
    // Set alert
    match = text.match(/alert me when ([\w.]+) is (above|below) \$?([\d.]+)/i);
    if (match) {
        const [, ticker, direction, price] = match;
        const newAlert = { ticker: ticker.toUpperCase(), direction, price: parseFloat(price) };
        // Remove any existing alert for the same ticker
        setAlerts(prev => [...prev.filter(a => a.ticker !== newAlert.ticker), newAlert]);
        addMessage('ai', `Alert set: I will notify you when ${newAlert.ticker} goes ${direction} $${newAlert.price}.`);
        return true;
    }

    // Analyze the most recent chart
    if (text.match(/analyze the chart/i)) {
        if (lastChartData) {
            const analysisPoints = generateAnalysisFromData(lastChartData);
            const prompt = `As a financial analyst AI, take these data points about a stock chart and write a concise, professional analysis in a single paragraph. Mention concepts like support, resistance, and momentum. Data points: "${analysisPoints}"`;
            callGeminiAPI(prompt);
        } else {
            addMessage('ai', "Of course. Please generate a chart first by asking me to 'chart [ticker]'.");
        }
        return true;
    }

    // Chart a stock
    match = text.match(/(?:chart|graph) ([\w.]+)/i);
    if (match) {
        const ticker = match[1].toUpperCase();
        const mockData = Array.from({ length: 30 }, (_, i) => {
            const date = new Date();
            date.setDate(date.getDate() - (29 - i));
            return {
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                price: 150 + Math.random() * 20 - 10 + i * 0.5 + (ticker.charCodeAt(0) % 10),
            };
        });
        setLastChartData({ticker, data: mockData}); // Store the data for analysis
        addMessage('ai', null, { type: 'chart', chartData: mockData, ticker });
        return true;
    }

    return false;
  };

  const handleSend = () => {
    const trimmedInput = input.trim();
    if (trimmedInput === '') return;

    addMessage('user', trimmedInput);
    
    if(!handleLocalCommands(trimmedInput)) {
        callGeminiAPI(trimmedInput);
    }
    
    setInput('');
  };

  const handleMic = () => {
    if (!recognitionRef.current) {
        showToast({ variant: "destructive", title: "Unsupported Browser", description: "Speech recognition is not available." });
        return;
    }
    if (!isListening) {
      recognitionRef.current.start();
      setIsListening(true);
      showToast({ title: "🎤 Microphone Enabled", description: "PRIV is now listening." });
    } else {
      recognitionRef.current.stop();
      setIsListening(false);
      showToast({ title: "🎤 Microphone Disabled" });
    }
  };

  const handleCamera = useCallback(async () => {
    if (!isCameraOn) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        setIsCameraOn(true);
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        showToast({ title: "📹 Camera Enabled", description: "Facial sentiment analysis is active." });
      } catch (err) {
        showToast({ variant: "destructive", title: "📹 Camera Access Denied", description: "Please enable camera access." });
      }
    } else {
      setIsCameraOn(false);
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
        videoRef.current.srcObject = null;
      }
      showToast({ title: "📹 Camera Disabled" });
    }
  }, [isCameraOn]);

  const AssistantAvatar = ({ onClick }) => (
    <motion.div
        className="fixed bottom-4 right-4 z-50 cursor-pointer w-20 h-20 rounded-full glass-morphism p-1 group"
        onClick={onClick}
        whileHover={{ scale: 1.1 }}
        transition={{ type: 'spring', stiffness: 300 }}
    >
        <div className="w-full h-full rounded-full overflow-hidden border-2 border-green-500/50 relative">
            <img alt="PRIV AI Assistant" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=1000&auto=format&fit=crop" />
            <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors duration-300"></div>
        </div>
        <motion.div 
          className="absolute inset-0 border-2 border-green-400 rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear"}}
        />
    </motion.div>
  );

  return (
    <>
      <CustomStyles />
      <AnimatePresence>
        <Toast message={toast} onDismiss={() => setToast(null)} />
      </AnimatePresence>

      <AnimatePresence>
        {!isOpen && <AssistantAvatar onClick={() => setIsOpen(true)} />}
      </AnimatePresence>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed bottom-0 right-0 sm:bottom-4 sm:right-4 w-full h-full sm:w-96 sm:h-[80vh] sm:max-h-[700px] glass-morphism rounded-none sm:rounded-2xl z-50 flex flex-col overflow-hidden"
          >
            <header className="flex items-center justify-between p-4 border-b border-green-500/20 flex-shrink-0">
              <div className="flex items-center space-x-3">
                <Bot className="w-6 h-6 text-green-400" />
                <h2 className="font-bold text-lg gradient-text">PRIV</h2>
              </div>
              <button aria-label="Close chat" className="p-1 rounded-full hover:bg-white/10" onClick={() => setIsOpen(false)}>
                <X className="w-5 h-5" />
              </button>
            </header>

            <div className="flex-1 p-4 space-y-4 overflow-y-auto scrollbar-hide">
              {messages.map((msg, index) => (
                <div key={index} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                  {msg.sender === 'ai' && <BrainCircuit className="w-6 h-6 text-green-400 flex-shrink-0 mt-1" />}
                  <div className={`max-w-[80%] p-3 rounded-xl text-sm whitespace-pre-wrap ${msg.sender === 'user' ? 'bg-blue-500/30' : 'bg-green-500/20'}`}>
                    {msg.text && <p dangerouslySetInnerHTML={{ __html: msg.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />}
                    {msg.type === 'chart' && <SimpleStockChart data={msg.chartData} ticker={msg.ticker} />}
                  </div>
                </div>
              ))}
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
            
            {isCameraOn && (
              <div className="relative h-24 bg-black/50 flex-shrink-0">
                <video ref={videoRef} autoPlay muted className="w-full h-full object-cover" />
                <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                  <p className="text-xs text-white/80">AGI Facial Sentiment Analysis: Active</p>
                </div>
              </div>
            )}

            <footer className="p-4 border-t border-green-500/20 flex-shrink-0">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder={isListening ? "Listening..." : "Ask PRIV anything..."}
                  className="flex-1 bg-transparent border border-gray-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                 <button aria-label="Toggle Text-to-Speech" onClick={() => setIsTtsEnabled(!isTtsEnabled)} className={`p-2 rounded-full transition-colors ${isTtsEnabled ? 'text-green-400 bg-green-500/20' : 'hover:bg-white/10'}`}>
                    <Volume2 className="w-5 h-5" />
                 </button>
                 <button aria-label="Toggle microphone" onClick={handleMic} className={`p-2 rounded-full transition-colors ${isListening ? 'text-green-400 bg-green-500/20 listening-glow' : 'hover:bg-white/10'}`}>
                  <Mic className="w-5 h-5" />
                </button>
                <button aria-label="Toggle camera" onClick={handleCamera} className={`p-2 rounded-full transition-colors ${isCameraOn ? 'text-green-400 bg-green-500/20' : 'hover:bg-white/10'}`}>
                  <Video className="w-5 h-5" />
                </button>
                <button aria-label="Send message" onClick={handleSend} className="p-2 rounded-full bg-green-500 hover:bg-green-600 transition-colors disabled:bg-gray-500 disabled:cursor-not-allowed" disabled={!input.trim() || isTyping}>
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </footer>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default PrivAssistant;


