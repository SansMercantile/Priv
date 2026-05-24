import React, { useState, useEffect } from "react";
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
  ChevronUp 
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

const GLOBAL_CALENDAR_EVENTS: CalendarEvent[] = [
  {
    id: 1,
    time: "12:30 UTC",
    date: "May 22, 2026",
    country: "USA",
    currency: "USD",
    event: "Core Retail Sales (MoM) (Apr)",
    impact: "HIGH",
    previous: "0.2%",
    forecast: "0.4%",
    actual: "0.6%",
    state: "positive",
    assessment: "US retail patterns represent incredibly resilient consumer spend lines, reinforcing a longer hawk horizon for the FOMC."
  },
  {
    id: 2,
    time: "08:00 UTC",
    date: "May 21, 2026",
    country: "EUR",
    currency: "EUR",
    event: "HCOB Eurozone Manufacturing PMI (May)",
    impact: "HIGH",
    previous: "45.7",
    forecast: "46.2",
    actual: "47.4",
    state: "positive",
    assessment: "European industrial sectors beat down contraction models. Provides temporary backing strength to local EUR spot indices."
  },
  {
    id: 3,
    time: "06:00 UTC",
    date: "May 20, 2026",
    country: "GBR",
    currency: "GBP",
    event: "Core CPI Inflation (YoY) (Apr)",
    impact: "HIGH",
    previous: "3.5%",
    forecast: "2.1%",
    actual: "2.3%",
    state: "negative",
    assessment: "Sticky UK services CPI exceeds forecasts. Restricts immediate Bank of England rate easing targets, keeping Sterling firm."
  },
  {
    id: 4,
    time: "23:30 UTC",
    date: "May 21, 2026",
    country: "JPN",
    currency: "JPY",
    event: "National Core CPI (YoY) (Apr)",
    impact: "HIGH",
    previous: "2.6%",
    forecast: "2.2%",
    actual: "2.2%",
    state: "neutral",
    assessment: "Inflation perfectly aligns with central bank targets. Steady pressure remains on BoJ for minor rate hikes in Q3 session."
  },
  {
    id: 5,
    time: "02:00 UTC",
    date: "May 21, 2026",
    country: "NZD",
    currency: "NZD",
    event: "RBNZ Interest Rate Decision",
    impact: "HIGH",
    previous: "5.50%",
    forecast: "5.50%",
    actual: "5.50%",
    state: "neutral",
    assessment: "Reserve Bank of New Zealand issued hawk warnings, delaying rate-cuts to early 2027. Kiwi holds value spreads."
  },
  {
    id: 6,
    time: "01:30 UTC",
    date: "May 21, 2026",
    country: "AUS",
    currency: "AUD",
    event: "Employment Change (Apr)",
    impact: "HIGH",
    previous: "-5.8k",
    forecast: "20.0k",
    actual: "38.5k",
    state: "positive",
    assessment: "Extremely tight labor statistics. Validates RBA's decision to maintain high-yield rates longer than peer Western banks."
  },
  {
    id: 7,
    time: "12:30 UTC",
    date: "May 21, 2026",
    country: "CAN",
    currency: "CAD",
    event: "Retail Sales (MoM) (Mar)",
    impact: "MEDIUM",
    previous: "-0.1%",
    forecast: "0.0%",
    actual: "-0.6%",
    state: "negative",
    assessment: "Canadian retail contraction points to high level of consumer strain, supporting case for an upcoming Bank of Canada easing path."
  },
  {
    id: 8,
    time: "18:00 UTC",
    date: "May 20, 2026",
    country: "USA",
    currency: "USD",
    event: "FOMC Meeting Minutes",
    impact: "HIGH",
    previous: "---",
    forecast: "---",
    actual: "Hawkish",
    state: "neutral",
    assessment: "Minutes emphasize consensus on rigid inflation barriers. Capital reallocations safely rotate toward high-yielding bills."
  },
  {
    id: 9,
    time: "14:00 UTC",
    date: "May 25, 2026",
    country: "USA",
    currency: "USD",
    event: "New Home Sales (MoM) (May)",
    impact: "MEDIUM",
    previous: "-8.6%",
    forecast: "2.1%",
    actual: "---",
    state: "pending",
    assessment: "Core real estate indices continue a soft contraction. Outperformance would trigger equity buying blocks."
  },
  {
    id: 10,
    time: "09:00 UTC",
    date: "May 28, 2026",
    country: "EUR",
    currency: "EUR",
    event: "ECB Interest Rate Decision",
    impact: "HIGH",
    previous: "4.50%",
    forecast: "4.25%",
    actual: "---",
    state: "pending",
    assessment: "High probability of standard 25bps ease. Focus centers on forward-looking comments relative to Euro carry pressure."
  },
  {
    id: 11,
    time: "07:00 UTC",
    date: "May 29, 2026",
    country: "CHE",
    currency: "CHF",
    event: "KOF Leading Indicators (May)",
    impact: "MEDIUM",
    previous: "101.8",
    forecast: "102.1",
    actual: "---",
    state: "pending",
    assessment: "Swiss forward indicators remain rigid. Suggests persisting Swiss Franc safe-haven hedge activity."
  },
  {
    id: 12,
    time: "12:30 UTC",
    date: "Jun 05, 2026",
    country: "USA",
    currency: "USD",
    event: "Non-Farm Employment Change (NFP)",
    impact: "HIGH",
    previous: "175k",
    forecast: "185k",
    actual: "---",
    state: "pending",
    assessment: "SANS core trigger point. Major labor reports printing below 160k acts as powerful federal policy easing catalyst."
  },
  {
    id: 13,
    time: "12:30 UTC",
    date: "Jun 10, 2026",
    country: "USA",
    currency: "USD",
    event: "Core CPI Inflation (YoY)",
    impact: "HIGH",
    previous: "3.6%",
    forecast: "3.5%",
    actual: "---",
    state: "pending",
    assessment: "Inherent inflation tracker. Reading above 3.5% will keep treasury rates locked at peaks until late winter sessions."
  }
];

export default function News({ demoMode }: { demoMode?: boolean }) {
  const [activeTab, setActiveTab] = useState<"NEWS" | "CALENDAR">("NEWS");
  
  // Articles filters
  const [filter, setFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [realArticles, setRealArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // Economic Calendar filters
  const [calendarCountry, setCalendarCountry] = useState<string>("All");
  const [calendarImpact, setCalendarImpact] = useState<string>("All");
  const [calendarQuery, setCalendarQuery] = useState<string>("");
  const [expandedEvents, setExpandedEvents] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setLoading(true);
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
      .catch(err => console.error("Error fetching live briefs:", err))
      .finally(() => setLoading(false));
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
  const filteredEvents = GLOBAL_CALENDAR_EVENTS.filter(ev => {
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
          {loading ? (
            <RefreshCw className="w-3.5 h-3.5 text-amber-500 animate-spin" />
          ) : (
            <Globe className="w-3.5 h-3.5 text-white/50" />
          )}
          <span className="text-white/60">
            {activeTab === "NEWS" 
              ? `${articles.length} INTELLIGENCE BRIEFS ACTIVE` 
              : `${GLOBAL_CALENDAR_EVENTS.length} MACRO INDICATORS STREAMING`}
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
                      <button className="flex items-center space-x-1 border border-white/10 bg-white/5 hover:bg-white hover:text-black py-1.5 px-3 rounded text-xs select-none transition duration-200 cursor-pointer text-white">
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
                        No macroeconomic calendar entries found in active search parameters.
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
    </div>
  );
}
