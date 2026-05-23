import React, { useState, useEffect } from "react";
import { Newspaper, Bell, ArrowUpRight, Search } from "lucide-react";
import apiClient from "../api/apiClient";
import { DEMO_NEWS_ARTICLES } from "../data/demoMocks";

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

export default function News({ demoMode }: { demoMode?: boolean }) {
  const [filter, setFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      if (demoMode) {
        if (!cancelled) {
          setArticles(DEMO_NEWS_ARTICLES as Article[]);
          setLoading(false);
        }
        return;
      }
      try {
        const resp = await apiClient.get("/api/v1/news/articles", { limit: 30 });
        const raw = resp?.articles || [];
        const mapped: Article[] = raw.map((a: Record<string, unknown>, i: number) => ({
          id: i + 1,
          title: String(a.title || "Untitled"),
          source: String(a.source || "Feed"),
          time: String(a.published || "recent"),
          sentiment: (a.sentiment === "positive"
            ? "Bullish"
            : a.sentiment === "negative"
              ? "Bearish"
              : "Neutral") as Article["sentiment"],
          summary: String(a.summary || a.description || ""),
          readTime: "3 min read",
          tags: Array.isArray(a.tags) ? (a.tags as string[]) : ["Market"],
        }));
        if (!cancelled) setArticles(mapped);
      } catch (e) {
        console.error(e);
        if (!cancelled) setArticles([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [demoMode]);

  const filteredArticles = articles.filter(art => {
    const matchesFilter = filter === "All" || art.tags.includes(filter) || art.sentiment === filter;
    const matchesSearch = art.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          art.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          art.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const getSentimentStyle = (sentiment: string) => {
    if (sentiment === "Bullish") return "text-emerald-500 border-emerald-500/20 bg-emerald-500/5";
    if (sentiment === "Bearish") return "text-rose-500 border-rose-500/20 bg-rose-500/5";
    return "text-amber-500 border-amber-500/20 bg-amber-500/5";
  };

  return (
    <div className="space-y-6">
      {/* Dynamic Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center">
            <Newspaper className="w-7 h-7 mr-3 text-white/70" />
            Tactical Briefings & News
          </h1>
          <p className="text-white/40 text-xs mt-1 font-light">
            {demoMode ? "Demo intelligence briefs" : "Live feed from /api/v1/news"}
          </p>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-white/5 rounded border border-white/10 font-mono text-xs">
          <Bell className="w-3.5 h-3.5 text-white/50 animate-bounce" />
          <span className="text-white/60">5 INTELLIGENCE BRIEFS ACTIVE</span>
        </div>
      </div>

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
        {loading ? (
          <div className="p-12 text-center font-mono text-xs text-stone-500">Loading briefings…</div>
        ) : filteredArticles.length === 0 ? (
          <div className="p-12 text-center rounded border border-white/10 bg-neutral-900/10 font-mono text-xs text-stone-500">
            No active briefs found matching filter query in current timeline epoch.
          </div>
        ) : (
          filteredArticles.map((art) => (
            <div 
              key={art.id} 
              className="metric-card p-6 rounded border border-white/10 relative overflow-hidden group transition duration-300 hover:border-white/20"
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
                  
                  <h3 className="text-xl font-medium text-white tracking-tight leading-snug group-hover:text-[#f8fafc] transition-colors">
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
  );
}
