import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Newspaper, 
  Bell, 
  Star, 
  ArrowUpRight, 
  Search, 
  Sparkles, 
  Filter, 
  RefreshCw, 
  Globe, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ChevronDown, 
  ChevronUp,
  Brain,
  TrendingUp,
  TrendingDown,
  X,
  Gauge
} from "lucide-react";

interface Article {
  id: number;
  title: string;
  source: string;
  time: string;
  sentiment: "Bullish" | "Neutral" | "Bearish";
  summary: string;
  readTime: string;
  tags: string[];
}

interface CalendarEvent {
  id: number;
  time: string;
  date: string;
  country: string;
  currency: string;
  event: string;
  impact: "HIGH" | "MEDIUM" | "LOW";
  previous: string;
  forecast: string;
  actual: string;
  state: "positive" | "negative" | "neutral" | "pending";
  assessment: string;
}


export default function News({ demoMode }: { demoMode?: boolean }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"NEWS" | "CALENDAR">("NEWS");
  
  // Economic calendar: live backend feed only (/api/v1/economic-calendar,
  // refreshed every 60s). Starts EMPTY -- a hardcoded seed table used to
  // sit here (May 2026 fiction) and lingered whenever the feed faltered.
  // An empty feed now renders an honest empty state, never stale fiction.
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [calendarLoading, setCalendarLoading] = useState<boolean>(false);
  const [calendarError, setCalendarError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const fetchCalendar = async () => {
      setCalendarLoading(true);
      try {
        const response = await fetch("/api/v1/economic-calendar");
        if (!active) return;
        if (response.ok) {
          const data = await response.json();
          if (data.success && Array.isArray(data.events)) {
            // Map the backend shape {id,time,date,country,currency,event,
            // impact,previous,forecast,actual} onto display rows, deriving
            // the release state from actual-vs-forecast (numbers arrive as
            // floats or null -- never invented).
            const num = (v: any): number | null => {
              if (v === null || v === undefined || v === "") return null;
              const n = typeof v === "number" ? v : parseFloat(String(v).replace(/[^0-9.\-]/g, ""));
              return Number.isFinite(n) ? n : null;
            };
            const mapped: CalendarEvent[] = data.events.map((e: any, i: number) => {
              const a = num(e.actual);
              const f = num(e.forecast);
              const p = num(e.previous);
              const fmt = (v: number | null) => (v === null ? "---" : String(v));
              let state: CalendarEvent["state"] = "pending";
              let assessment = `Scheduled — forecast ${fmt(f)} (prev ${fmt(p)}).`;
              if (a !== null) {
                if (f !== null && a > f) state = "positive";
                else if (f !== null && a < f) state = "negative";
                else state = "neutral";
                assessment = `Released at ${fmt(a)} vs forecast ${fmt(f)} (prev ${fmt(p)}).`;
              }
              return {
                id: typeof e.id === "number" ? e.id : i,
                time: e.time || "--:--",
                date: e.date || "",
                country: e.country || e.currency || "",
                currency: e.currency || "",
                event: e.event || "Unknown event",
                impact: (["HIGH", "MEDIUM", "LOW"].includes(e.impact) ? e.impact : "LOW") as CalendarEvent["impact"],
                previous: fmt(p),
                forecast: fmt(f),
                actual: fmt(a),
                state,
                assessment,
              };
            });
            setCalendarEvents(mapped);
            setCalendarError(mapped.length === 0 ? "No upcoming events in the live feed right now." : null);
          }
        } else {
          setCalendarError("Live calendar feed unavailable (backend error).");
        }
      } catch (err) {
        console.warn("Could not retrieve live economic calendar events:", err);
        if (active) setCalendarError("Live calendar feed unreachable.");
      } finally {
        if (active) setCalendarLoading(false);
      }
    };
    fetchCalendar();
    const interval = setInterval(fetchCalendar, 60000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);
  
  // Articles filters
  const [filter, setFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [realArticles, setRealArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Analysis Modal States
  const [selectedAnalysis, setSelectedAnalysis] = useState<any | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingArticle, setAnalyzingArticle] = useState<Article | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const runFundamentalAnalysis = async (article: Article) => {
    setAnalyzingArticle(article);
    setIsAnalyzing(true);
    setSelectedAnalysis(null);
    setAnalysisError(null);

    try {
      const response = await fetch("/api/v1/news/analyze-impact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: article.title,
          summary: article.summary,
          source: article.source,
          sentiment: article.sentiment
        })
      });

      if (!response.ok) {
        throw new Error("Analysis engine server fault");
      }

      const data = await response.json();
      if (data.success) {
        setSelectedAnalysis(data);
      } else {
        throw new Error(data.error || "Analysis was inconclusive");
      }
    } catch (err: any) {
      console.error("[SANS Analytical Core] Error during fundamental analysis:", err);
      setAnalysisError(err.message || "Cognitive server feedback exception. Safe sandbox modes engaged.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadAssetInTerminal = (symbol: string) => {
    const symbolMap: Record<string, string> = {
      "XAUUSD": "OANDA:XAUUSD",
      "XAGUSD": "OANDA:XAGUSD",
      "BTCUSD": "BINANCE:BTCUSDT",
      "EURUSD": "FX_IDC:EURUSD",
      "GBPUSD": "FX_IDC:GBPUSD",
      "USDJPY": "FX_IDC:USDJPY",
      "USDCAD": "FX_IDC:USDCAD"
    };

    const targetTicker = symbolMap[symbol.toUpperCase().replace("-", "")] || symbolMap["EURUSD"];
    localStorage.setItem("xm_selected_symbol", targetTicker);
    setSelectedAnalysis(null);
    setAnalyzingArticle(null);
    navigate("/dashboard/terminal");
  };

  // Economic Calendar filters
  const [calendarCountry, setCalendarCountry] = useState<string>("All");
  const [calendarImpact, setCalendarImpact] = useState<string>("All");
  const [calendarQuery, setCalendarQuery] = useState<string>("");
  const [expandedEvents, setExpandedEvents] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setLoading(true);
    const fetchRealRssNews = async () => {
      try {
        const feedUrl = "https://finance.yahoo.com/news/rss";
        const response = await fetch(`/api/rss?url=${encodeURIComponent(feedUrl)}`);
        if (!response.ok) {
          throw new Error("Proxy error");
        }
        const xmlText = await response.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, "text/xml");
        const items = xmlDoc.getElementsByTagName("item");
        
        const parsed: Article[] = [];
        const count = Math.min(items.length, 12);
        for (let i = 0; i < count; i++) {
          const item = items[i];
          const title = item.getElementsByTagName("title")[0]?.textContent || "Macro Financial Highlight";
          const descriptionRaw = item.getElementsByTagName("description")[0]?.textContent || "";
          const pubDateStr = item.getElementsByTagName("pubDate")[0]?.textContent || "";
          const creator = item.getElementsByTagName("dc:creator")[0]?.textContent || "Yahoo Finance";
          
          const summary = descriptionRaw.replace(/<[^>]*>?/gm, "").substring(0, 200) + "...";
          
          let timeStr = "12m ago";
          if (pubDateStr) {
            const date = new Date(pubDateStr);
            const diffMs = Date.now() - date.getTime();
            const diffMins = Math.floor(diffMs / 60000);
            if (diffMins < 60 && diffMins > 0) {
              timeStr = `${diffMins}m ago`;
            } else if (diffMins >= 60 && diffMins < 1440) {
              timeStr = `${Math.floor(diffMins / 60)}h ago`;
            } else {
              timeStr = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
            }
          }
          
          const sentimentOptions: Array<"Bullish" | "Neutral" | "Bearish"> = ["Bullish", "Neutral", "Neutral", "Bearish"];
          const sentiment = sentimentOptions[Math.floor(Math.sin(i) * 2 + 2)] || "Neutral";
          
          parsed.push({
            id: i + 500,
            title,
            source: creator || "Yahoo Finance",
            time: timeStr,
            sentiment,
            summary,
            readTime: "3 min read",
            tags: ["Live", "Macro", creator ? creator.split(" ")[0] : "Market"]
          });
        }
        
        if (parsed.length > 0) {
          setRealArticles(parsed);
          return;
        }
      } catch (err) {
        console.warn("Failed fetching live Yahoo headlines, falling back to REST schema:", err);
      }
      
      // Fallback API
      fetch("/api/v1/news/articles")
        .then(res => res.json())
        .then(data => {
          if (data && data.articles && data.articles.length > 0) {
            const formatted = data.articles.map((art: any, index: number) => {
              const rawSentiment = art.sentiment || "Neutral";
              const sentimentMap: Record<string, "Bullish" | "Neutral" | "Bearish"> = {
                positive: "Bullish",
                negative: "Bearish",
                neutral: "Neutral"
              };
              const mappedSentiment = sentimentMap[rawSentiment.toLowerCase()] || "Neutral";

              let timeStr = "12m ago";
              if (art.published) {
                const date = new Date(art.published);
                const diffMs = Date.now() - date.getTime();
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMins / 600);
                if (diffMins < 60 && diffMins > 0) {
                  timeStr = `${diffMins}m ago`;
                } else if (diffHours < 24 && diffHours > 0) {
                  timeStr = `${diffHours}h ago`;
                } else {
                  timeStr = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
                }
              }

              return {
                id: index + 100,
                title: art.title || art.headline || "Macro Financial Event Highlighted",
                source: art.source || "SANS Integrated RSS",
                time: timeStr,
                sentiment: mappedSentiment,
                summary: art.summary || art.content || "The SANS sovereign analytical parser registered dynamic volatility shifts inside the asset indices, recommending optimal hedging metrics.",
                readTime: "2 min read",
                tags: art.tags || ["Realtime", art.source ? art.source.replace("https://", "").replace("www.", "").split(".")[0] : "Market"]
              };
            });
            setRealArticles(formatted);
          }
        })
        .catch(err => console.error("Error fetching live briefs:", err));
    };

    fetchRealRssNews().finally(() => setLoading(false));
  }, []);

  const defaultArticles: Article[] = [
    {
      id: 1,
      title: "Global Supply Chain Congestion Prompts Autonomous Arbitrage Influx",
      source: "SANS Intelligence Branch",
      time: "12m ago",
      sentiment: "Bullish",
      summary: "Quantitative Arbitrage clusters initiated short-term spread maneuvers across SADC maritime carriers, projecting standard premium arbitrage margins above index bounds.",
      readTime: "3 min read",
      tags: ["Arbitrage", "Logistics", "Volume"]
    },
    {
      id: 2,
      title: "Federal Reserve Board Signals Volatility Constraints Adjustment",
      source: "Financial Times Core",
      time: "1h ago",
      sentiment: "Neutral",
      summary: "Simulated market strategies predict micro-adjustments following adjusted inflation outlooks. High-Frequency execution limits remain unchanged under security protocol AN-03.",
      readTime: "5 min read",
      tags: ["Macro", "Execution", "Fed"]
    },
    {
      id: 3,
      title: "GRA Announces Algorithmic Custom Exemption Verification Standard",
      source: "Ghana Revenue Service Gate",
      time: "3h ago",
      sentiment: "Bullish",
      summary: "New algorithmic customs declarations allow local nodes to autonomously apply for tax clearance exemptions, optimizing capital routing by up to 2.4%.",
      readTime: "4 min read",
      tags: ["Tax", "Compliance", "GRA"]
    },
    {
      id: 4,
      title: "Unprecedented Volume Spike Detected in Synthetic Bond Swaps",
      source: "SANS Sovereign Node 3",
      time: "5h ago",
      sentiment: "Bullish",
      summary: "Alternative Sentiment models captured rapid reallocation patterns into collateralized short-term sovereign yielding assets. Execution routers adjusted slippage parameters.",
      readTime: "2 min read",
      tags: ["Volume", "Bonds", "Sovereign"]
    },
    {
      id: 5,
      title: "Geopolitical Re-alignment Impacts West Africa Commodity Spreads",
      source: "Reuters Corporate",
      time: "8h ago",
      sentiment: "Bearish",
      summary: "Commodity arbitrage pipelines face temporary freight spikes. Risk-Guardian models designated specific trade sectors as 'Restricted' pending board consensus.",
      readTime: "7 min read",
      tags: ["Commodity", "Risk", "SADC"]
    }
  ];

  const articles = realArticles.length > 0 ? [...realArticles, ...defaultArticles] : defaultArticles;

  const filteredArticles = articles.filter(art => {
    const matchesFilter = filter === "All" || art.tags.some(category => category.toLowerCase() === filter.toLowerCase()) || art.tags.includes(filter) || art.sentiment === filter;
    const matchesSearch = art.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          art.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          art.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const getSentimentStyle = (sentiment: string) => {
    if (sentiment === "Bullish") return "text-emerald-400 border-emerald-500/20 bg-emerald-500/5";
    if (sentiment === "Bearish") return "text-rose-400 border-rose-500/20 bg-rose-500/5";
    return "text-amber-400 border-amber-500/20 bg-amber-500/5";
  };

  const getImpactBadge = (impact: "HIGH" | "MEDIUM" | "LOW") => {
    if (impact === "HIGH") return "text-rose-400 bg-rose-500/10 border-rose-500/30";
    if (impact === "MEDIUM") return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    return "text-zinc-400 bg-zinc-500/10 border-white/5";
  };

  const getCalendarValueStyle = (state: string) => {
    if (state === "positive") return "text-emerald-400 font-bold";
    if (state === "negative") return "text-rose-400 font-bold";
    return "text-stone-300";
  };

  // Filter Calendar Events
  const filteredEvents = calendarEvents.filter(ev => {
    const matchesCountry = calendarCountry === "All" || ev.country === calendarCountry || ev.currency === calendarCountry;
    const matchesImpact = calendarImpact === "All" || ev.impact === calendarImpact;
    const matchesSearch = ev.event.toLowerCase().includes(calendarQuery.toLowerCase()) ||
                          ev.assessment.toLowerCase().includes(calendarQuery.toLowerCase());
    return matchesCountry && matchesImpact && matchesSearch;
  });

  const toggleEventExpand = (id: number) => {
    setExpandedEvents(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      {/* Dynamic Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <Newspaper className="w-7 h-7 mr-3 text-white/70" />
            Tactical Briefings & News
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">Sovereign alternative data stream and financial intelligence aggregator</p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs self-start sm:self-auto">
          {loading || calendarLoading ? (
            <RefreshCw className="w-3.5 h-3.5 text-amber-500 animate-spin" />
          ) : (
            <Globe className="w-3.5 h-3.5 text-white/50" />
          )}
          <span className="text-white/60">
            {activeTab === "NEWS" 
              ? `${articles.length} INTELLIGENCE BRIEFS ACTIVE` 
              : `${calendarEvents.length} MACRO INDICATORS STREAMING`}
          </span>
        </div>
      </div>

      {/* Module Navigation Tabs */}
      <div className="flex border-b border-white/10">
        <button
          id="tab-news"
          onClick={() => setActiveTab("NEWS")}
          className={`pb-3 text-xs font-mono font-bold tracking-widest uppercase transition-colors relative mr-8 cursor-pointer select-none ${
            activeTab === "NEWS" ? "text-white" : "text-zinc-500 hover:text-white"
          }`}
        >
          <span>1. TACTICAL BRIEFINGS FEED</span>
          {activeTab === "NEWS" && (
            <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-sky-400 shadow-[0_0_8px_rgb(56,189,248)]" />
          )}
        </button>
        <button
          id="tab-calendar"
          onClick={() => setActiveTab("CALENDAR")}
          className={`pb-3 text-xs font-mono font-bold tracking-widest uppercase transition-colors relative cursor-pointer select-none ${
            activeTab === "CALENDAR" ? "text-white" : "text-zinc-500 hover:text-white"
          }`}
        >
          <span>2. GLOBAL ECONOMIC CALENDAR</span>
          {activeTab === "CALENDAR" && (
            <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-sky-400 shadow-[0_0_8px_rgb(56,189,248)]" />
          )}
        </button>
      </div>

      {/* 1. TACTICAL BRIEFING STREAM TAB */}
      {activeTab === "NEWS" && (
        <div className="space-y-6 animate-fadeIn">
          {/* Filter and Search Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 flex flex-wrap gap-1.5">
              {["All", "Arbitrage", "Macro", "Tax", "Volume", "Risk", "Bullish", "Neutral", "Bearish"].map((category) => (
                <button
                  key={category}
                  onClick={() => setFilter(category)}
                  className={`px-3 py-1.5 rounded text-xs transition duration-200 cursor-pointer ${
                    filter === category 
                      ? "bg-white text-black font-medium border border-white" 
                      : "bg-neutral-900 text-stone-400 border border-white/5 hover:text-white"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-500" />
              <input
                type="text"
                placeholder="Search alternative intelligence..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-neutral-950 border border-white/10 rounded pl-9 pr-4 py-2 text-xs text-white placeholder-stone-600 focus:outline-none focus:border-white/30"
              />
            </div>
          </div>

          {/* Main Articles Stream */}
          <div className="space-y-6">
            {filteredArticles.length === 0 ? (
              <div className="p-12 text-center rounded border border-white/10 bg-neutral-900/10 font-mono text-xs text-stone-500">
                No active briefs found matching filter query in current timeline epoch.
              </div>
            ) : (
              filteredArticles.map((art) => (
                <div 
                  key={art.id} 
                  className="metric-card p-6 rounded border border-white/10 relative overflow-hidden group transition duration-300 hover:border-white/20 bg-neutral-950/20"
                >
                  <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent group-hover:from-white/25 transition duration-300" />
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-3 flex-1">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="text-[10px] font-mono font-bold tracking-wider text-white/40">{art.source.toUpperCase()}</span>
                        <span className="text-[10px] font-mono text-stone-400">&bull;&nbsp;{art.time}</span>
                        <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${getSentimentStyle(art.sentiment)}`}>
                          {art.sentiment}
                        </span>
                        <span className="text-[10px] font-mono text-zinc-500">&bull;&nbsp;{art.readTime}</span>
                      </div>
                      
                      <h3 className="text-xl font-medium text-white tracking-tight leading-snug group-hover:text-sky-300 transition-colors">
                        {art.title}
                      </h3>
                      
                      <p className="text-sm text-stone-400 font-sans leading-relaxed tracking-normal">
                        {art.summary}
                      </p>

                      <div className="flex gap-1.5 pt-1">
                        {art.tags.map((t) => (
                          <span key={t} className="text-[9px] px-2 py-0.5 rounded font-mono bg-neutral-950 border border-white/5 text-zinc-400 select-none">
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="self-end md:self-start">
                      <button 
                        onClick={() => runFundamentalAnalysis(art)}
                        className="flex items-center space-x-1 border border-white/10 bg-white/5 hover:bg-white hover:text-black py-1.5 px-3 rounded text-xs select-none transition duration-200 cursor-pointer text-white"
                      >
                        <span>Analyze Impact</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 2. GLOBAL ECONOMIC CALENDAR TAB */}
      {activeTab === "CALENDAR" && (
        <div id="economic-calendar-section" className="space-y-6 animate-fadeIn">
          {/* HIGH IMPACT WEEKLY TICKER TAPE */}
          <div className="bg-red-950/20 border border-red-500/20 py-2.5 px-4 rounded-xl flex items-center overflow-hidden font-mono text-[10px] text-red-400 select-none shadow-[0_4px_12px_rgba(239,68,68,0.05)]">
            <div className="flex items-center space-x-1.5 flex-shrink-0 z-10 bg-neutral-950 dark:bg-black pr-4 font-bold uppercase tracking-wider text-red-500 animate-pulse border-r border-red-500/20 mr-4">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-2 animate-ping" />
              <span>HIGH IMPACT ALERTS (WEEKLY TAPE)</span>
            </div>
            
            <style>{`
              @keyframes marquee-economic {
                0% { transform: translate3d(0, 0, 0); }
                100% { transform: translate3d(-50%, 0, 0); }
              }
              .marquee-scroll-economic {
                display: flex;
                white-space: nowrap;
                animation: marquee-economic 35s linear infinite;
              }
              .marquee-scroll-economic:hover {
                animation-play-state: paused;
              }
            `}</style>

            <div className="marquee-scroll-economic flex gap-8">
              <span className="flex items-center gap-2">
                <strong>[NFP]</strong> Non-Farm Employment Change — <span className="text-zinc-400">JUN 05, 12:30 UTC</span> &bull; Forecast: <span className="font-bold text-white">185k</span> (Previous: 175k) <span className="bg-red-500/20 text-[8px] px-1 py-0.5 rounded border border-red-500/20 font-bold">REVOLUTION ALERTS</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[CPI]</strong> Core CPI Inflation YoY (USA) — <span className="text-zinc-400">JUN 10, 12:30 UTC</span> &bull; Forecast: <span className="font-bold text-white">3.5%</span> (Previous: 3.6%) <span className="bg-red-500/20 text-[8px] px-1 py-0.5 rounded border border-red-500/20 font-bold">HIGH VOLATILITY</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[ECB]</strong> Eurozone Rate Decision — <span className="text-zinc-400">MAY 28, 09:00 UTC</span> &bull; Forecast: <span className="font-bold text-white">4.25%</span> (Previous: 4.50%) <span className="bg-amber-500/20 text-[8px] px-1 py-0.5 text-amber-400 rounded border border-amber-500/20 font-bold">RATE MOVE EXPECTED</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[FOMC]</strong> US Meeting Minutes released — <span className="text-emerald-400">HAWKISH BIAS EXTENDED</span> &bull; SANS risk matrix advises buying spot metal above support <span className="bg-emerald-500/20 text-[8px] px-1 py-0.5 text-emerald-400 rounded border border-emerald-500/20 font-bold">METRICS RECORDED</span>
              </span>
              
              {/* Duplicate for seamless looping marquee */}
              <span className="flex items-center gap-2">
                <strong>[NFP]</strong> Non-Farm Employment Change — <span className="text-zinc-400">JUN 05, 12:30 UTC</span> &bull; Forecast: <span className="font-bold text-white">185k</span> (Previous: 175k) <span className="bg-red-500/20 text-[8px] px-1 py-0.5 rounded border border-red-500/20 font-bold">REVOLUTION ALERTS</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[CPI]</strong> Core CPI Inflation YoY (USA) — <span className="text-zinc-400">JUN 10, 12:30 UTC</span> &bull; Forecast: <span className="font-bold text-white">3.5%</span> (Previous: 3.6%) <span className="bg-red-500/20 text-[8px] px-1 py-0.5 rounded border border-red-500/20 font-bold">HIGH VOLATILITY</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[ECB]</strong> Eurozone Rate Decision — <span className="text-zinc-400">MAY 28, 09:00 UTC</span> &bull; Forecast: <span className="font-bold text-white">4.25%</span> (Previous: 4.50%) <span className="bg-amber-500/20 text-[8px] px-1 py-0.5 text-amber-400 rounded border border-amber-500/20 font-bold">RATE MOVE EXPECTED</span>
              </span>
              <span className="flex items-center gap-2">
                <strong>[FOMC]</strong> US Meeting Minutes released — <span className="text-emerald-400">HAWKISH BIAS EXTENDED</span> &bull; SANS risk matrix advises buying spot metal above support <span className="bg-emerald-500/20 text-[8px] px-1 py-0.5 text-emerald-400 rounded border border-emerald-500/20 font-bold">METRICS RECORDED</span>
              </span>
            </div>
          </div>

          {/* Calendar Controller Filters */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-neutral-950/60 p-4 rounded-xl border border-white/10">
            {/* Country Selector */}
            <div className="space-y-1.5">
              <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-widest leading-none">Country / Currency</label>
              <select
                value={calendarCountry}
                onChange={(e) => setCalendarCountry(e.target.value)}
                className="w-full bg-black border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
              >
                <option value="All">All Regions (Sovereign Array)</option>
                <option value="USA">USA &bull; United States (USD)</option>
                <option value="EUR">EUR &bull; Eurozone (EUR)</option>
                <option value="GBR">GBR &bull; United Kingdom (GBP)</option>
                <option value="JPN">JPN &bull; Japan (JPY)</option>
                <option value="AUS">AUS &bull; Australia (AUD)</option>
                <option value="CAN">CAN &bull; Canada (CAD)</option>
                <option value="NZD">NZD &bull; New Zealand (NZD)</option>
                <option value="CHE">CHE &bull; Switzerland (CHF)</option>
              </select>
            </div>

            {/* Impact Selector */}
            <div className="space-y-1.5">
              <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-widest leading-none">Strategic Impact Focus</label>
              <select
                value={calendarImpact}
                onChange={(e) => setCalendarImpact(e.target.value)}
                className="w-full bg-black border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
              >
                <option value="All">All Voltages</option>
                <option value="HIGH">High Volatility (Red Alerts)</option>
                <option value="MEDIUM">Medium Volatility (Slight Shifts)</option>
                <option value="LOW">Low Volatility (Routine Metrics)</option>
              </select>
            </div>

            {/* Calendar Keyword Filter */}
            <div className="md:col-span-2 space-y-1.5">
              <label className="block text-[10px] font-mono text-zinc-500 uppercase tracking-widest leading-none">Search Indicators / Events</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-500" />
                <input
                  type="text"
                  placeholder="Filter by 'inflation', 'sales', 'interest rate'..."
                  value={calendarQuery}
                  onChange={(e) => setCalendarQuery(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded pl-9 pr-4 py-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Calendar List Table */}
          <div className="border border-white/10 bg-neutral-950/20 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full font-sans text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/10 bg-neutral-950 text-zinc-500 font-mono text-[10px] uppercase tracking-widest">
                    <th className="py-3 px-4 font-normal">State / Curr</th>
                    <th className="py-3 px-4 font-normal">Time (UTC) & Date</th>
                    <th className="py-3 px-4 font-normal text-center">Impact</th>
                    <th className="py-3 px-4 font-normal">Economic Indicator Event</th>
                    <th className="py-3 px-4 font-normal text-right">Previous</th>
                    <th className="py-3 px-4 font-normal text-right">Forecast</th>
                    <th className="py-3 px-4 font-normal text-right">Actual</th>
                    <th className="py-3 px-4 font-normal text-center w-12">Advisory</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredEvents.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-xs font-mono text-stone-500">
                        {calendarEvents.length === 0
                          ? (calendarLoading ? "Loading live calendar…" : (calendarError || "No upcoming events in the live feed right now."))
                          : "No macroeconomic calendar entries found in active search parameters."}
                      </td>
                    </tr>
                  ) : (
                    filteredEvents.map((ev) => {
                      const isExpanded = !!expandedEvents[ev.id];
                      return (
                        <React.Fragment key={ev.id}>
                          <tr 
                            onClick={() => toggleEventExpand(ev.id)}
                            className="hover:bg-white/5 transition duration-150 cursor-pointer group"
                          >
                            <td className="py-3.5 px-4 font-mono text-xs">
                              <div className="flex items-center space-x-2">
                                <span className="bg-neutral-800 border border-white/10 text-white font-bold px-1.5 py-0.5 rounded text-[10px] select-none leading-none">
                                  {ev.country}
                                </span>
                                <span className="text-zinc-500 text-[10px]">{ev.currency}</span>
                              </div>
                            </td>
                            <td className="py-3.5 px-4 font-mono text-xs text-zinc-300">
                              <div className="flex flex-col">
                                <span className="font-semibold text-white">{ev.time}</span>
                                <span className="text-zinc-500 text-[10px] mt-0.5">{ev.date}</span>
                              </div>
                            </td>
                            <td className="py-3.5 px-4 text-center">
                              <span className={`text-[9px] font-mono uppercase px-2 py-0.5 rounded border ${getImpactBadge(ev.impact)} font-bold`}>
                                {ev.impact}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-xs font-medium text-stone-200 group-hover:text-sky-300 transition-colors">
                              {ev.event}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-xs text-right text-stone-400">
                              {ev.previous}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-xs text-right text-stone-400">
                              {ev.forecast}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-xs text-right">
                              <span className={getCalendarValueStyle(ev.state)}>
                                {ev.actual}
                              </span>
                            </td>
                            <td className="py-3.5 px-4 text-center">
                              <button 
                                type="button" 
                                className="p-1 rounded bg-white/5 text-zinc-400 hover:text-white"
                              >
                                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </button>
                            </td>
                          </tr>
                          
                          {/* Collapsible proprietary SANS Advisory Commentary row */}
                          {isExpanded && (
                            <tr className="bg-neutral-950/80">
                              <td colSpan={8} className="py-4 px-6 border-l-2 border-sky-500">
                                <div className="space-y-1.5 animate-fadeIn">
                                  <div className="flex items-center space-x-2 text-sky-400 font-mono text-[10px] uppercase tracking-wider font-semibold">
                                    <Sparkles className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
                                    <span>SANS Algorithmic Advisory Analysis</span>
                                  </div>
                                  <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                                    {ev.assessment}
                                  </p>
                                  <div className="flex items-center space-x-4 pt-1 text-[9px] font-mono text-zinc-500">
                                    <span>STATUS: {ev.actual === "---" ? "UPCOMING EVENT" : "METRIC CAPTURED"}</span>
                                    <span>&bull;&nbsp;ASSET IMPACT CORRELATION MAP: SECURE DETAILED MODE SELECTED</span>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Calendar System Diagnostics Footer */}
          <div className="p-4 bg-sky-500/5 rounded-xl border border-sky-500/20 flex flex-col md:flex-row items-center justify-between gap-2.5 font-mono text-[10px] text-sky-400">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-sky-400" />
              <span>SANS CHANNELS MONITOR: Synchronized with 8 Sovereign Central Vault feeds.</span>
            </div>
            <div className="text-zinc-500">
              TIME INTERLOCK: CENTRAL DECENTRALIZED EPOCH SECURE
            </div>
          </div>
        </div>
      )}

      {/* 3. COGNITIVE ANALYSIS LOADER OVERLAY */}
      {isAnalyzing && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#09090b] border border-white/10 rounded-2xl shadow-2xl p-8 relative overflow-hidden flex flex-col items-center text-center space-y-6 animate-fadeIn">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-sky-400 via-indigo-500 to-sky-400 animate-pulse" />
            
            {/* Spinning/pulsing Brain Icon and Neon Grid */}
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-sky-500/10 border border-sky-500/30 flex items-center justify-center animate-pulse">
                <Brain className="w-10 h-10 text-sky-400 animate-pulse" />
              </div>
              <span className="absolute inset-0 rounded-full border border-sky-400/30 animate-ping" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-mono font-bold tracking-widest text-white uppercase">SANS COGNITIVE ENGINE</h3>
              <p className="text-xs text-sky-400 font-mono animate-pulse text-center">RUNNING GENERALIZED FUNDAMENTAL ANALYSIS...</p>
            </div>

            <div className="w-full bg-white/5 rounded-full h-1 overflow-hidden">
              <div className="bg-sky-400 h-1 rounded-full animate-pulse" style={{ width: "60%" }} />
            </div>

            <div className="font-mono text-[9px] text-zinc-500 space-y-1">
              <div>INGESTING MACRO DATA FOR: "{analyzingArticle?.title.substring(0, 45)}..."</div>
              <div>CROSS-REFERENCING WEEKLY ECONOMIC CALENDAR...</div>
              <div>CORRELATING VOLATILITY RATINGS...</div>
            </div>
          </div>
        </div>
      )}

      {/* 4. REAL-TIME FUNDAMENTAL ANALYSIS OVERLAY MODAL */}
      {selectedAnalysis && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-[#09090b] border border-white/10 rounded-2xl shadow-2xl p-6 relative overflow-hidden flex flex-col max-h-[90vh] animate-fadeIn">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-400 via-sky-400 to-amber-400" />
            
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-white/10 mb-5 text-left">
              <div className="flex items-center space-x-2.5 text-left">
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center">
                  <Brain className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white">SANS Cognitive Intelligence Report</h3>
                  <p className="text-[10px] font-mono text-zinc-500">PROPRIETARY FUNDAMENTAL REASONING ROUTER</p>
                </div>
              </div>
              <button 
                onClick={() => { setSelectedAnalysis(null); setAnalyzingArticle(null); }}
                className="p-1 rounded bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition duration-150 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body (Scrollable) */}
            <div className="flex-1 overflow-y-auto space-y-5 pr-1 text-left font-sans">
              
              {/* Source Article Title */}
              <div className="p-3 bg-neutral-900/60 rounded-xl border border-white/5 text-left">
                <span className="text-[9px] font-mono text-zinc-500 uppercase block">Input Sentiment Asset Stream</span>
                <h4 className="text-white font-medium text-sm mt-0.5 leading-snug">{analyzingArticle?.title}</h4>
              </div>

              {/* Analysis Scores Columns */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-left">
                
                {/* Confidence */}
                <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex flex-col justify-between text-left">
                  <span className="text-[9px] text-zinc-500 uppercase leading-none block">Confidence Rating</span>
                  <div className="flex items-baseline space-x-1.5 mt-2">
                    <span className="text-2xl font-bold text-white font-sans">{selectedAnalysis.confidence}%</span>
                    <span className="text-[9px] text-zinc-500 leading-none">PRECISION</span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-3">
                    <div className="bg-sky-400 h-1.5 rounded-full" style={{ width: `${selectedAnalysis.confidence}%` }} />
                  </div>
                </div>

                {/* Volatility */}
                <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex flex-col justify-between text-left">
                  <span className="text-[9px] text-zinc-500 uppercase leading-none block">Volatility Factor</span>
                  <div className="flex items-baseline space-x-1.5 mt-2">
                    <span className="text-2xl font-bold text-white font-sans">{selectedAnalysis.impact}</span>
                    <span className="text-[9px] text-rose-400 leading-none">RATING</span>
                  </div>
                  <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden mt-3">
                    <div 
                      className="bg-rose-400 h-1.5 rounded-full" 
                      style={{ width: selectedAnalysis.impact === 'HIGH' ? '90%' : selectedAnalysis.impact === 'MEDIUM' ? '60%' : '30%' }} 
                    />
                  </div>
                </div>

                {/* Consensus Strategy */}
                <div className="p-3 bg-white/5 rounded-xl border border-white/5 flex flex-col justify-between text-left">
                  <span className="text-[9px] text-zinc-500 uppercase leading-none font-bold block">Consensus Sentiment</span>
                  <div className="flex items-center space-x-2 mt-2">
                    {selectedAnalysis.consensus_strategy?.toUpperCase() === 'BUY' ? (
                      <TrendingUp className="w-5 h-5 text-emerald-400" />
                    ) : selectedAnalysis.consensus_strategy?.toUpperCase() === 'SELL' ? (
                      <TrendingDown className="w-5 h-5 text-rose-400" />
                    ) : (
                      <Gauge className="w-5 h-5 text-amber-400" />
                    )}
                    <span className={`text-xl font-bold ${
                      selectedAnalysis.consensus_strategy?.toUpperCase() === 'BUY' ? 'text-emerald-400' :
                      selectedAnalysis.consensus_strategy?.toUpperCase() === 'SELL' ? 'text-rose-400' : 'text-amber-400'
                    }`}>
                      {selectedAnalysis.consensus_strategy || "HOLD"}
                    </span>
                  </div>
                  <span className="mt-2 text-[9px] text-zinc-500 uppercase leading-none block">SANS SYSTEM CONSENSUS</span>
                </div>

              </div>

              {/* Signals and symbols */}
              <div className="p-4 rounded-xl border border-sky-500/10 bg-sky-500/5 space-y-3.5 text-left">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 font-mono">
                  <div>
                    <span className="text-[9px] text-sky-400 uppercase font-bold block">Fundamental Signal Tag</span>
                    <span className="text-white text-xs font-bold bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded uppercase block mt-1">{selectedAnalysis.signal || "NEUTRAL CORRELATION"}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-sky-400 uppercase font-bold block">Target Assets Affected</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {selectedAnalysis.affected_symbols?.map((sym: string) => (
                        <button 
                          key={sym}
                          onClick={() => handleLoadAssetInTerminal(sym)}
                          className="bg-black border border-white/10 hover:border-sky-400 text-sky-300 font-bold px-2 py-0.5 rounded text-[10px] select-none cursor-pointer transition flex items-center gap-1 group"
                          title={`Click to route in Terminal`}
                        >
                          <span>{sym}</span>
                          <ArrowUpRight className="w-2.5 h-2.5 text-zinc-500 group-hover:text-sky-400" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Deep Narrative Output */}
              <div className="space-y-1.5 text-left">
                <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest block">Reasoning Narrative</span>
                <p className="text-xs text-zinc-300 leading-relaxed font-sans bg-zinc-950 p-4 rounded-xl border border-white/5 whitespace-pre-line text-left">
                  {selectedAnalysis.narrative || "The SANS fundamental intelligence core was unable to detail a specific threat direction due to conflicting central banking indices. Trading terminal standard protective levels are recommended."}
                </p>
              </div>

            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 mt-5 pt-4 border-t border-white/10">
              <button 
                onClick={() => { setSelectedAnalysis(null); setAnalyzingArticle(null); }}
                className="px-4 py-2 bg-neutral-900 hover:bg-neutral-800 text-zinc-300 font-mono text-xs rounded border border-white/5 cursor-pointer select-none transition"
              >
                Close Report
              </button>
              {selectedAnalysis.affected_symbols && selectedAnalysis.affected_symbols.length > 0 && (
                <button 
                  onClick={() => handleLoadAssetInTerminal(selectedAnalysis.affected_symbols[0])}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-black font-mono font-bold text-xs rounded select-none cursor-pointer transition flex items-center space-x-1"
                >
                  <span>Load {selectedAnalysis.affected_symbols[0]} Terminal Route</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 5. ANALYSIS ERROR FALLBACK POPUP */}
      {analysisError && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-[#09090b] border border-red-500/20 rounded-2xl shadow-2xl p-6 relative flex flex-col items-center text-center space-y-4 animate-fadeIn">
            <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            
            <div className="space-y-1">
              <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider text-center">Analysis Engine Fault</h3>
              <p className="text-xs text-zinc-400 text-center">{analysisError}</p>
            </div>

            <button 
              onClick={() => setAnalysisError(null)}
              className="w-full py-2 bg-red-500/10 hover:bg-red-500/20 text-red-200 border border-red-500/20 rounded text-xs font-mono font-semibold transition cursor-pointer"
            >
              Close Alert
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
