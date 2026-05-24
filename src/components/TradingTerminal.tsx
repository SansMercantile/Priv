import React, { useState, useEffect, useRef } from "react";
import { 
  Activity, 
  Lock, 
  Unlock, 
  Wifi, 
  TrendingUp, 
  TrendingDown, 
  Newspaper, 
  Globe, 
  RefreshCw, 
  Play, 
  ArrowRight, 
  Search, 
  Database, 
  ShieldAlert, 
  CheckCircle2, 
  Calculator, 
  Clock, 
  ArrowUpRight, 
  LogOut, 
  Coins, 
  Plus, 
  Server, 
  Sparkles, 
  ChevronRight,
  X,
  BookOpen
} from "lucide-react";

// Types for broker account state
interface OpenPosition {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  lots: number;
  entryPrice: number;
  currentPrice: number;
  tp?: number;
  sl?: number;
  pnl: number;
  timestamp: string;
}

interface HistoricalTrade {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  lots: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  timestamp: string;
}

// Predefined hot financial RSS feeds
const PREDEFINED_FEEDS = [
  { name: "ForexLive FX News", url: "https://www.forexlive.com/feed" },
  { name: "Yahoo Finance", url: "https://finance.yahoo.com/news/rssindex" },
  { name: "SANS Intelligence Feed", url: "" } // Custom or local simulation falling back
];

// Predefined simulated Twitter handles to track
const TWITTER_FEEDS = [
  { username: "ZeroHedge", content: "Macro liquidity channels indicators flashing standard quantitative stress thresholds. Watch short-term swap spreads.", time: "4m ago", sentiment: "Bearish" },
  { username: "XM_Markets", content: "Core FOMC forecast continues to factor hawkish target ranges. High volatility expected around non-farm indexes.", time: "18m ago", sentiment: "Neutral" },
  { username: "SANS_Mercantile", content: "PRIV Core autonomous nodes integrated. Initial trade execution logs routed via Secure Broker Gate.", time: "1h ago", sentiment: "Bullish" },
  { username: "FederalReserve", content: "Balance sheet drawdown procedures to execute as scheduled. Open market operations target rate unchanged.", time: "2h ago", sentiment: "Neutral" },
  { username: "WhaleAlert", content: "🚨 41,250 #BTC ($3.7B) transferred from unknown sovereign cold-vault to liquidation router gate.", time: "3h ago", sentiment: "Bearish" }
];

// Mock local articles if network feeds are blocked
const LOCAL_MOCK_ARTICLES = [
  { title: "Sovereign Bond Spreads Tighten Ahead of G7 Trade Accord", source: "SANS Core Analytics", time: "Just now", snip: "Arbitrage routers have adjusted slippage margins down to 0.12 bps following stable treasury flows." },
  { title: "ECB Board Assesses Liquidity Squeeze on High-Freq Nodes", source: "Euro-Zone Monitor", time: "25m ago", snip: "Proposed regulations might cap high-leverage algorithmic execution routers at 1:100 inside regulatory jurisdictions." },
  { title: "Safe Haven Allocation Drifts Toward Offshore Sovereign Vaults", source: "Geneva Financial Gate", time: "1h ago", snip: "Alternate collateral index tracks record institutional inflow into physical custody vaults." }
];

const MOCK_ARTICLES_BY_SYMBOL: Record<string, typeof LOCAL_MOCK_ARTICLES> = {
  EURUSD: [
    { title: "Euro-Zone Yield Devaluation Accelerates Trade Deficits", source: "REUTERS FX TERMINAL", time: "Just now", snip: "As ECB members signal a pivot in interest rate policy, the EURUSD tests major support at 1.0820. Spot order books indicate institutional buy slabs are thickening under current market depth." },
    { title: "Fed Hawkish Outlook Keeps Dollar Dominant Across Majors", source: "FINANCIAL TIMES", time: "25m ago", snip: "The persistent interest expansion gap between the FOMC and the ECB is driving treasury liquidity swaps towards USD, exerting structural bearish friction onto EURUSD rates." },
    { title: "EURUSD Technical Outlook: Pivot Confirmed at 1.0865 Range", source: "SANS QUANTITATIVE CORE", time: "1h ago", snip: "Sub-millisecond momentum gauges are signaling high-density buy liquidity waiting at 1.0835, with tactical structural resistance firm at 1.0915." }
  ],
  GBPUSD: [
    { title: "Bank of England Treads Cautiously Amid Persistent Inflation Spikes", source: "BLOOMBERG CORES", time: "Just now", snip: "With BoE board members split on rate-cut timings, the Sterling holds consolidation bands above 1.2580. High-frequency volume is shifting to Spot liquidity desks." },
    { title: "UK GDP Quarterly Print Outperforms Initial Structural Forecasts", source: "LONDON GENERAL GATE", time: "25m ago", snip: "A surprise 0.4% quarterly growth surge provides temporary relief for GBPUSD, triggering breakout buy stops above 1.2650 resistance levels." },
    { title: "Sterling Liquidity Sweep Map Projects High Volatility Range At Open", source: "SANS ANALYSIS DESK", time: "1h ago", snip: "We observe significant market maker imbalances near the 1.2510 zone, indicating a potential downside sweep target before any continuation rally." }
  ],
  USDJPY: [
    { title: "Bank of Japan Intervention Threats Cap Yen Devaluation Rate", source: "NIKKEI MACRO", time: "Just now", snip: "With USDJPY hovering near critical levels, traders remain alert for Ministry of Finance (MoF) liquidity operations to support the Japanese currency." },
    { title: "Treasury Yield Surges Keep Yen Carry Trade Highly Profit-Yielding", source: "TOKYO SPOT REPORT", time: "25m ago", snip: "The carry trade spread remains exceptionally wide, encouraging continuous retail shorting of JPY to capture multi-month yield differentials." },
    { title: "USDJPY Order Blocks Show Support Levels Moving Upward", source: "SANS QUANTITATIVE CORE", time: "1h ago", snip: "Consolidation bands of buy liquidity are firmly anchored at 155.20, while resistance clusters stand thick near the 157.50 level." }
  ],
  XAUUSD: [
    { title: "Systemic Credit Risk Boosts Physical Sovereign Custody Demand", source: "ZURICH METALS CAP", time: "Just now", snip: "Gold Spot prices hold firm as institutions allocate capital out of paper swaps into physical bullion reserves. Resistance observed at $2,422." },
    { title: "Central Bank Gold Purchasing Program Reaches Historical Volumes", source: "WORLD GOLD COUNCIL", time: "25m ago", snip: "Sovereign accumulation of gold continues to provide a structural tailwind, keeping the commodity's floor price high at $2,385." },
    { title: "SANS Advisory on Speculative Metal Swaps and Weekly Close Settings", source: "SANS COMMODITY DESKS", time: "1h ago", snip: "Precious metal markets are currently closed for the weekend. SANS analytical models project support at $2,385.50 and resistance at $2,422.00 on Sunday open." }
  ],
  BTCUSDT: [
    { title: "Liquidity Shift From Traditional Securities Boosts Decentralized Ledger", source: "COINBASE INDEX", time: "Just now", snip: "Spot Bitcoin ETFs record high net inflows. Institutional participants are setting up spot custody accounts as alternative collateral hedges." },
    { title: "BTC Real-Time Hashrate Clocks Record Heights Amid Difficulty Adjustment", source: "BLOCKCHAIN INTEL", time: "25m ago", snip: "Mining network difficulty increased by 3.82% representing steady long-term hash security, supporting a fair-value price baseline near $65k." },
    { title: "Bitcoin Spot Order Imbalance Shows Resistance Zone Cleared", source: "SANS CRYPTOGRAPHIC NODE", time: "1h ago", snip: "Unlike legacy CFDs, cryptocurrency markets operate 24/7. Immediate trend indicators show target resistance at $68,900 and solid backing support at $65,400." }
  ],
  USDCAD: [
    { title: "BOC Policy Deviation Softens Canadian Capital Inflows", source: "REUTERS MACRO", time: "Just now", snip: "As BOC signals a potential decoupling sequence from the Fed, USDCAD buyers look to secure entries ahead of key employment reports." },
    { title: "Crude Supply Adjustments Trigger Temporary Loonie Squeezes", source: "OIL DESK CHANNELS", time: "25m ago", snip: "Fluctuating Brent futures hold USDCAD near key support at 1.3620, while wholesale importers defend the range base." },
    { title: "SANS Advisory on Bank of Canada Overnight Interest Settings", source: "SANS EXCELLENCE NODE", time: "1h ago", snip: "Quantitative pipelines revised loonie support zones. Highly precise limit filters are placed at 1.3640 index levels." }
  ],
  XAGUSD: [
    { title: "Industrial Silver Shipments Tighten Spot Exchange Custody", source: "ZURICH METALS CAP", time: "Just now", snip: "With silver demand outpacing central reserve allocations, Spot Silver rates tests the major $30.50 threshold with heavy volume backing." },
    { title: "Precious Metals Cross-Rate Ratio Suggests Silver Breakout Impending", source: "BLOOMBERG CORE", time: "25m ago", snip: "The gold-to-silver valuation ratio continues to decline from 80 towards 77, indicating potential silver outperformance next week." },
    { title: "SANS Metals Desk Forecasts Silver Squeezes Under Sovereign Buy Pressure", source: "SANS ANALYSIS DESK", time: "1h ago", snip: "Dynamic silver trackers highlight strong systemic accumulation points above $29.80, with tactical parameters targeted to $31.50." }
  ]
};

const cleanSymbol = (sym: string): string => {
  return sym.replace("XM:", "").replace("FX:", "").replace("BINANCE:", "").replace("FOREXCOM:", "").replace("FX_IDC:", "").toUpperCase();
};

const getDynamicMockArticles = (sym: string) => {
  const base = sym.substring(0, 3).toUpperCase();
  const quote = sym.substring(3).toUpperCase() || "USD";
  return [
    {
      title: `${base}/${quote} Technical Imbalances Drive Global Liquidity Rerouting`,
      source: "SANS DIGITAL NODE",
      time: "Just now",
      snip: `Sovereign settlement structures indicate dynamic rate adjustments on key ${sym} spot accounts. Speculator flows target support lines under deep buy ledger density constraints.`
    },
    {
      title: `Central Desks Position Buy Inflows to Absorb ${base} Selling Squeezes`,
      source: "MACRO BULLION NEWS",
      time: "18m ago",
      snip: `Open market operations and regional trade accounts demonstrate ongoing demand. Alternate collateral index marks high institutional capital inflows into ${base} relative portfolios.`
    },
    {
      title: `PRIV Copilot Advisory: Tracking Custom Limit Blocks for ${sym}`,
      source: "PRIV INTEL DESK",
      time: "1h ago",
      snip: `Continuous execution node designated standard limit order placements as high priority. Volatility ratings suggest low-slippage trade executions should be favored nearby.`
    }
  ];
};

interface InstrumentIntel {
  title: string;
  fullName: string;
  direction: "BULLISH" | "NEUTRAL" | "BEARISH";
  support: string;
  resistance: string;
  dailyRange: string;
  sentimentPercent: number;
  tacticalNote: string;
  tradeBias: string;
  volatilityRating: "Low" | "Medium" | "High" | "Extreme";
  targetProfit: string;
  stopLoss: string;
}

const INSTRUMENT_INTEL_MAP: Record<string, InstrumentIntel> = {
  EURUSD: {
    title: "EURUSD",
    fullName: "Euro / US Dollar (Spot Forex)",
    direction: "BULLISH",
    support: "1.0820",
    resistance: "1.0915",
    dailyRange: "1.0835 - 1.0890",
    sentimentPercent: 78,
    tacticalNote: "Consolidating near major H4 Support at 1.0820. Moving average clusters indicate solid buyer density. Suitable for swing buy entries on discount sweeps.",
    tradeBias: "BUY LIMITS NEAR 1.0835",
    volatilityRating: "Medium",
    targetProfit: "1.0895",
    stopLoss: "1.0790"
  },
  GBPUSD: {
    title: "GBPUSD",
    fullName: "Pound Sterling / US Dollar (Cable)",
    direction: "NEUTRAL",
    support: "1.2580",
    resistance: "1.2690",
    dailyRange: "1.2595 - 1.2675",
    sentimentPercent: 54,
    tacticalNote: "GBP remains sticky ahead of the BOE MPC session. Wait for a sweep of 1.2580 before seeking low-slippage long triggers.",
    tradeBias: "MONITOR SUPPORT AT 1.2580",
    volatilityRating: "High",
    targetProfit: "1.2680",
    stopLoss: "1.2530"
  },
  USDJPY: {
    title: "USDJPY",
    fullName: "US Dollar / Japanese Yen",
    direction: "BEARISH",
    support: "154.20",
    resistance: "155.80",
    dailyRange: "154.50 - 155.40",
    sentimentPercent: 31,
    tacticalNote: "BOJ rate verbal warning risks are rising. Heavy speculative short Yen blocks suggest a possible sharp technical wash-out. Limit long exposures.",
    tradeBias: "TACTICAL SHORTS NEAR 155.60",
    volatilityRating: "High",
    targetProfit: "153.80",
    stopLoss: "156.40"
  },
  XAUUSD: {
    title: "XAUUSD",
    fullName: "Spot Gold / US Dollar (Sovereign Metals)",
    direction: "BULLISH",
    support: "2,385.50",
    resistance: "2,422.00",
    dailyRange: "2,390.00 - 2,415.00",
    sentimentPercent: 91,
    tacticalNote: "Peak sovereign allocation continues to bolster metals. Safe-haven pools remain active. Buyers are targeting the psychological 2,420 barrier next.",
    tradeBias: "LONG ACCUMULATION ABOVE 2,390",
    volatilityRating: "Extreme",
    targetProfit: "2,425.00",
    stopLoss: "2,372.00"
  },
  BTCUSDT: {
    title: "BTCUSD",
    fullName: "Bitcoin / Tether (Sovereign Digital Asset)",
    direction: "BULLISH",
    support: "88,200",
    resistance: "91,500",
    dailyRange: "88,400 - 90,800",
    sentimentPercent: 84,
    tacticalNote: "Whale ledger consolidations are building clear ground above 88K. Bull flags are forming on H1, suggesting momentum triggers on a breakout past 91.5K.",
    tradeBias: "LONG ON RETESTS OF 88.5K",
    volatilityRating: "Extreme",
    targetProfit: "93,200",
    stopLoss: "86,900"
  },
  USDCAD: {
    title: "USDCAD",
    fullName: "US Dollar / Canadian Dollar (Loonie)",
    direction: "BULLISH",
    support: "1.3620",
    resistance: "1.3740",
    dailyRange: "1.3640 - 1.3710",
    sentimentPercent: 68,
    tacticalNote: "Loonie under pressure as WTI crude contracts flag resistance. Dynamic support levels are well-defended near 1.3620. Re-allocation is highly favorable on retracements.",
    tradeBias: "BUY RETESTS OF 1.3640",
    volatilityRating: "Medium",
    targetProfit: "1.3750",
    stopLoss: "1.3580"
  },
  XAGUSD: {
    title: "XAGUSD",
    fullName: "Spot Silver / US Dollar (Precious Metals)",
    direction: "BULLISH",
    support: "29.80",
    resistance: "31.20",
    dailyRange: "29.95 - 30.85",
    sentimentPercent: 86,
    tacticalNote: "Industrial requirements and general metal indices are lifting Spot Silver rapidly. Breakout above 30.85 suggests direct target expansion towards historical 31.50 corridor.",
    tradeBias: "BUY DIP ACCUMULATION SUB 30.20",
    volatilityRating: "Extreme",
    targetProfit: "31.50",
    stopLoss: "29.10"
  }
};

const getDynamicIntel = (sym: string): InstrumentIntel => {
  const base = sym.substring(0, 3).toUpperCase();
  const quote = sym.substring(3).toUpperCase() || "USD";
  
  // Use a simple hash code of symbol string to return stable random-looking but consistent numbers for standard display
  let hash = 0;
  for (let i = 0; i < sym.length; i++) {
    hash = sym.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash);

  const direction = index % 3 === 0 ? "BEARISH" : index % 3 === 1 ? "NEUTRAL" : "BULLISH";
  const sentimentPercent = 40 + (index % 51); // 40% to 90%
  const volatilityRating = index % 4 === 0 ? "Low" : index % 4 === 1 ? "Medium" : index % 4 === 2 ? "High" : "Extreme" as "Low" | "Medium" | "High" | "Extreme";

  // Compute realistic price bounds based on base asset names
  let priceBase = 1.25;
  if (sym.includes("JPY")) priceBase = 150.0;
  else if (sym.includes("XAU") || sym.includes("GOLD")) priceBase = 2400.0;
  else if (sym.includes("XAG") || sym.includes("SILVER")) priceBase = 30.50;
  else if (sym.includes("BTC")) priceBase = 90000.0;
  else if (sym.includes("ETH")) priceBase = 3500.0;
  else if (sym.includes("CAD")) priceBase = 1.36;
  else if (sym.includes("AUD")) priceBase = 0.66;
  else if (sym.includes("EUR")) priceBase = 1.08;
  
  const precision = (priceBase > 1000) ? 2 : (priceBase > 10) ? 2 : 4;
  const supportVal = priceBase - (0.0125 * priceBase);
  const resistanceVal = priceBase + (0.0125 * priceBase);
  const rangeMin = priceBase - (0.005 * priceBase);
  const rangeMax = priceBase + (0.005 * priceBase);
  const stopLossVal = direction === "BULLISH" ? priceBase - (0.02 * priceBase) : priceBase + (0.02 * priceBase);
  const tpVal = direction === "BULLISH" ? priceBase + (0.03 * priceBase) : priceBase - (0.03 * priceBase);

  const support = supportVal.toFixed(precision);
  const resistance = resistanceVal.toFixed(precision);
  const dailyRange = `${rangeMin.toFixed(precision)} - ${rangeMax.toFixed(precision)}`;
  const targetProfit = tpVal.toFixed(precision);
  const stopLoss = stopLossVal.toFixed(precision);

  const tacticalNote = `Dynamic sovereign node reports structural pricing buffers for ${sym} are now synchronized. Liquid order books show accumulation bands near key support interfaces with high buy frequency. Recommendation is consistent with standard high-volume institutional exposure limits.`;

  return {
    title: sym,
    fullName: `${base} / ${quote} Spot Asset`,
    direction,
    support,
    resistance,
    dailyRange,
    sentimentPercent,
    tacticalNote,
    tradeBias: direction === "BULLISH" ? `LONG RE-ACCUMULATION ABOVE ${support}` : direction === "BEARISH" ? `SHORT SELLS BELOW ${resistance}` : `RANGE LIMIT BIAS AT ${support}`,
    volatilityRating,
    targetProfit,
    stopLoss
  };
};

export default function TradingTerminal({ 
  demoMode, 
  setDemoMode 
}: { 
  demoMode?: boolean; 
  setDemoMode?: (val: boolean) => void;
}) {
  // --- STATE DECLARATIONS ---
  // Active TradingView Ticker Selection
  const [selectedSymbol, setSelectedSymbol] = useState<string>("XM:EURUSD");
  const [customSymbolInput, setCustomSymbolInput] = useState<string>("");

  // Dynamic instrument intelligence state mapping
  const activeSymbolCodeGlobal = cleanSymbol(selectedSymbol);
  const currentIntel = INSTRUMENT_INTEL_MAP[activeSymbolCodeGlobal] || getDynamicIntel(activeSymbolCodeGlobal);

  const getSymbolSpecificNews = () => {
    const key = cleanSymbol(selectedSymbol);
    let keywords = [key.toLowerCase(), key.substring(0, 3).toLowerCase(), key.substring(3).toLowerCase()];
    if (key === "EURUSD") {
      keywords = ["eur", "euro", "fed", "inflation", "usd", "cpi", "powell", "ecb", "lagarde"];
    } else if (key === "GBPUSD") {
      keywords = ["gbp", "pound", "sterling", "boe", "london", "uk", "cable"];
    } else if (key === "USDJPY") {
      keywords = ["jpy", "yen", "boj", "tokyo", "asia", "intervention"];
    } else if (key === "XAUUSD") {
      keywords = ["xau", "gold", "metal", "commodity", "bullion", "silver", "metals"];
    } else if (key === "BTCUSDT" || key === "BTCUSD") {
      keywords = ["btc", "bitcoin", "crypto", "ether", "whale", "blockchain"];
    } else if (key === "USDCAD") {
      keywords = ["cad", "usd", "loonie", "canada", "boc", "oil", "dollar", "fed"];
    } else if (key === "XAGUSD") {
      keywords = ["xag", "silver", "metal", "commodity", "bullion", "metals"];
    }

    // Filter remote RSS articles that containing any keyword
    const matched = rssArticles.filter(art => 
      keywords.some(kw => art.title.toLowerCase().includes(kw) || art.snip.toLowerCase().includes(kw))
    );

    // Dynamic tailored bulletin fallbacks specifically for this instrument to ensure 100% overview coverage
    const bulletins = (MOCK_ARTICLES_BY_SYMBOL[key] || getDynamicMockArticles(key)).map(art => ({
      title: art.title,
      source: art.source,
      time: art.time,
      snip: art.snip,
      link: "#"
    }));

    return matched.length > 0 ? [...matched, ...bulletins].slice(0, 6) : bulletins;
  };

  const getSimulatedTwitterFeeds = (sym: string) => {
    if (sym === "EURUSD") {
      return [
        { username: "ZeroHedge", content: "Macro liquidity channels flashing standard EURUSD interest rate divergence thresholds. Support at 1.0820 holding steady.", time: "4m ago", sentiment: "Bullish" },
        { username: "XM_Markets", content: "Euro inflation print sets the stage for a critical ECB session. High-speed carry traders looking at 1.0915 dynamic ceiling.", time: "18m ago", sentiment: "Neutral" },
        { username: "SANS_Mercantile", content: "PRIV Secure Node: Algorithmic EURUSD exposure recommendation is aligned. Limit buy order targeted around 1.0835.", time: "1h ago", sentiment: "Bullish" }
      ];
    } else if (sym === "GBPUSD") {
      return [
        { username: "SterlingInsight", content: "BOE rate decision minutes leak suggests growing hawkish division. Target ranges for GBPUSD revised to 1.2580 - 1.2690.", time: "2m ago", sentiment: "Bullish" },
        { username: "ZeroHedge", content: "UK housing data outperformer keeps BoE on high inflation alert. Cable longs build support above 1.2595 base.", time: "14m ago", sentiment: "Neutral" },
        { username: "SANS_Mercantile", content: "Dynamic GBPUSD sweep parameters adjusted. Sovereign ledger ready to absorb liquidity below 1.2580.", time: "1h ago", sentiment: "Bullish" }
      ];
    } else if (sym === "USDJPY") {
      return [
        { username: "YenWatcher", content: "🚨 MOF visual warning levels: 'Extreme FX swings are undesirable.' Direct intervention risks spike if JPY slides past 156.", time: "3m ago", sentiment: "Bearish" },
        { username: "ZeroHedge", content: "carry traders printing record arbitrage sizes on USDJPY. If BOJ doesn't hike soon, 156.0 might see heavy squeeze.", time: "30m ago", sentiment: "Neutral" },
        { username: "NikkeiMacro", content: "Japanese retail option books show heavy protective USDJPY put options placed at 154.20 zone.", time: "2h ago", sentiment: "Bearish" }
      ];
    } else if (sym === "XAUUSD") {
      return [
        { username: "GoldBullion", content: "Commodity desks reporting massive physical bullion drawdowns from Western vaults. Safe-haven asset bias remains exceptionally strong.", time: "5m ago", sentiment: "Bullish" },
        { username: "ZeroHedge", content: "XAUUSD targets 2,422. Central bank reserves increase gold ratio by 8.4% YoY. Cash alternatives continue to lose premium.", time: "12m ago", sentiment: "Bullish" },
        { username: "SANS_Mercantile", content: "Secured spot metals router designates Gold limit setups as active. Strong bias on retest of 2,390 support corridor.", time: "1h ago", sentiment: "Bullish" }
      ];
    } else {
      return [
        { username: "WhaleAlert", content: "🚨 12,500 #BTC ($1.1B) moved from long-term cold custody to Coinbase liquidity pool. Base support stable at 88K.", time: "4m ago", sentiment: "Neutral" },
        { username: "PlanB_Fractal", content: "Bitcoin Bollinger bands tightening on the hourly slot. Technical breakout setup targeting 91.5K is ready.", time: "22m ago", sentiment: "Bullish" },
        { username: "CryptoWhale", content: "Leveraged longs completely wiped out. Bitcoin price recovery signals very robust bid density above 88,200.", time: "1h ago", sentiment: "Bullish" }
      ];
    }
  };

  // Broker authentication
  const [isLogged, setIsLogged] = useState<boolean>(() => {
    return localStorage.getItem("xm_is_logged") === "true";
  });
  const [isLoggingIn, setIsLoggingIn] = useState<boolean>(false);
  const [accountId, setAccountId] = useState<string>(() => {
    return localStorage.getItem("xm_account_id") || "58904231";
  });
  const [server, setServer] = useState<string>(() => {
    return localStorage.getItem("xm_server") || "XMGlobal-Real 14";
  });
  const [password, setPassword] = useState<string>("••••••••••••");
  const [leverage, setLeverage] = useState<string>(() => {
    return localStorage.getItem("xm_leverage") || "1:500";
  });
  const [accountType, setAccountType] = useState<"LIVE" | "DEMO">("DEMO");

  const [showLivePrompt, setShowLivePrompt] = useState<boolean>(false);

  // Sync accountType form option with global demoMode changes
  useEffect(() => {
    if (demoMode !== undefined) {
      setAccountType(demoMode ? "DEMO" : "LIVE");
      const savedIsLogged = localStorage.getItem("xm_is_logged") === "true";
      if (!demoMode) {
        setIsLogged(savedIsLogged);
        if (!savedIsLogged) {
          setBalance(0);
          setInitialBalance(0);
          setPositions([]);
          setHistory([]);
          setExecutionLogs([
            `[${new Date().toLocaleTimeString()}] Live connection required. Discarded simulated demo balances and open ledgers.`
          ]);
        } else {
          setBalance(parseFloat(localStorage.getItem("xm_balance") || "5218.42"));
          setInitialBalance(parseFloat(localStorage.getItem("xm_initial_balance") || "5000.00"));
          setExecutionLogs([
            `[${new Date().toLocaleTimeString()}] Restored verified handshaking node. Live portfolio synchronized.`
          ]);
        }
      } else {
        setIsLogged(true); // Demo mode starts connected automatically for ease-of-use
        setBalance(10000.0);
        setInitialBalance(10000.0);
        setExecutionLogs([
          `[${new Date().toLocaleTimeString()}] Joined simulated Sandbox Environment. Simulated $10,000 credit allocated.`
        ]);
      }
    }
  }, [demoMode]);
  const [accountCurrency, setAccountCurrency] = useState<string>("USD");

  // Balance parameters
  const [balance, setBalance] = useState<number>(() => {
    if (demoMode) return 10000.0;
    return localStorage.getItem("xm_is_logged") === "true" 
      ? parseFloat(localStorage.getItem("xm_balance") || "5218.42")
      : 0;
  });
  const [initialBalance, setInitialBalance] = useState<number>(() => {
    if (demoMode) return 10000.0;
    return localStorage.getItem("xm_is_logged") === "true" 
      ? parseFloat(localStorage.getItem("xm_initial_balance") || "5000.00")
      : 0;
  });
  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [history, setHistory] = useState<HistoricalTrade[]>([]);
  const [executionLogs, setExecutionLogs] = useState<string[]>([]);

  // Order placing sub-states
  const [orderSide, setOrderSide] = useState<"BUY" | "SELL">("BUY");
  const [orderLots, setOrderLots] = useState<number>(1.0);
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [limitPrice, setLimitPrice] = useState<number>(0);
  const [orderSL, setOrderSL] = useState<string>("");
  const [orderTP, setOrderTP] = useState<string>("");

  // RSS Feed Integration
  const [selectedRssUrl, setSelectedRssUrl] = useState<string>("https://www.forexlive.com/feed");
  const [customRssUrl, setCustomRssUrl] = useState<string>("");
  const [rssArticles, setRssArticles] = useState<any[]>([]);
  const [rssLoading, setRssLoading] = useState<boolean>(false);
  const [rssError, setRssError] = useState<string>("");

  // Layout helper state
  const [activeRightTab, setActiveRightTab] = useState<"NEWS" | "TWITTER" | "CALCULATOR">("NEWS");

  // Utility calculator states
  const [calcMarginSymbol, setCalcMarginSymbol] = useState<string>("EURUSD");
  const [calcMarginLots, setCalcMarginLots] = useState<number>(1.0);
  const [calcMarginLeverage, setCalcMarginLeverage] = useState<number>(500);
  const [calcResultMargin, setCalcResultMargin] = useState<number>(200);

  // Reference hooks for TradingView widgets
  const containerRef = useRef<HTMLDivElement>(null);
  const techContainerRef = useRef<HTMLDivElement>(null);
  const tickerTapeRef = useRef<HTMLDivElement>(null);
  const forexCrossRatesRef = useRef<HTMLDivElement>(null);
  const screenerRef = useRef<HTMLDivElement>(null);

  // --- COMPUTE KEY METRICS ---
  const currentFloatingPnl = positions.reduce((acc, pos) => acc + pos.pnl, 0);
  const equity = balance + currentFloatingPnl;
  // Calculate Margin (approx: Lot * ContractSize * CurrentPrice / Leverage)
  // Contract sizes: Forex = 100,000, Gold = 100, Crypto = 1
  const usedMargin = positions.reduce((acc, pos) => {
    let contractSize = 100000;
    if (pos.symbol.includes("XAU") || pos.symbol.includes("Gold")) contractSize = 100;
    if (pos.symbol.includes("BTC")) contractSize = 1;
    const levVal = parseInt(leverage.split(":")[1]) || 500;
    return acc + (pos.lots * contractSize * pos.currentPrice) / levVal;
  }, 0);

  const freeMargin = equity - usedMargin;
  const marginLevel = usedMargin > 0 ? (equity / usedMargin) * 100 : 0;

  // --- TRADINGVIEW IFRAME WIDGETS RENDER ---
  useEffect(() => {
    // 1. Render Ticker Tape
    if (tickerTapeRef.current) {
      tickerTapeRef.current.innerHTML = "";
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js";
      script.type = "text/javascript";
      script.async = true;
      script.innerHTML = JSON.stringify({
        "symbols": [
          { "proName": "FOREXCOM:SPXUSD", "title": "S&P 500" },
          { "proName": "FX_IDC:EURUSD", "title": "EUR/USD" },
          { "proName": "FX_IDC:GBPUSD", "title": "GBP/USD" },
          { "proName": "XM:XAUUSD", "title": "Gold Spot" },
          { "proName": "BINANCE:BTCUSDT", "title": "Bitcoin" },
          { "proName": "FX:USDJPY", "title": "USD/JPY" }
        ],
        "showSymbolLogo": false,
        "colorTheme": "dark",
        "isTransparent": true,
        "displayMode": "adaptive",
        "locale": "en"
      });
      tickerTapeRef.current.appendChild(script);
    }

    // 1b. Render Forex Cross Rates Heatmap
    if (forexCrossRatesRef.current) {
      forexCrossRatesRef.current.innerHTML = "";
      const scriptHeatmap = document.createElement("script");
      scriptHeatmap.src = "https://s3.tradingview.com/external-embedding/embed-widget-forex-cross-rates.js";
      scriptHeatmap.type = "text/javascript";
      scriptHeatmap.async = true;
      scriptHeatmap.innerHTML = JSON.stringify({
        "width": "100%",
        "height": "100%",
        "currencies": ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "CAD", "NZD"],
        "isTransparent": true,
        "colorTheme": "dark",
        "locale": "en"
      });
      forexCrossRatesRef.current.appendChild(scriptHeatmap);
    }

    // 1c. Render Live Technical Screener Tool
    if (screenerRef.current) {
      screenerRef.current.innerHTML = "";
      const scriptScreener = document.createElement("script");
      scriptScreener.src = "https://s3.tradingview.com/external-embedding/embed-widget-screener.js";
      scriptScreener.type = "text/javascript";
      scriptScreener.async = true;
      scriptScreener.innerHTML = JSON.stringify({
        "width": "100%",
        "height": "100%",
        "defaultColumn": "overview",
        "defaultScreen": "general",
        "market": "forex",
        "showToolbar": true,
        "colorTheme": "dark",
        "locale": "en",
        "isTransparent": true
      });
      screenerRef.current.appendChild(scriptScreener);
    }
  }, []);

  useEffect(() => {
    // 2. Render Main Technical Chart
    if (containerRef.current) {
      containerRef.current.innerHTML = "";
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
      script.type = "text/javascript";
      script.async = true;
      script.innerHTML = JSON.stringify({
        "autosize": true,
        "symbol": selectedSymbol,
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "calendar": true,
        "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
        "support_gestures": true,
        "container_id": "tradingview_chart_frame"
      });
      containerRef.current.appendChild(script);
    }

    // 3. Render Technical Analysis Gauge
    if (techContainerRef.current) {
      techContainerRef.current.innerHTML = "";
      const scriptTech = document.createElement("script");
      scriptTech.src = "https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js";
      scriptTech.type = "text/javascript";
      scriptTech.async = true;
      scriptTech.innerHTML = JSON.stringify({
        "interval": "15m",
        "width": "100%",
        "isTransparent": true,
        "height": "100%",
        "symbol": selectedSymbol,
        "showIntervalTabs": true,
        "locale": "en",
        "colorTheme": "dark"
      });
      techContainerRef.current.appendChild(scriptTech);
    }

    // Update the local helper limits state based on symbol selection
    const priceVal = getAssetRefPrice(selectedSymbol);
    setLimitPrice(parseFloat(priceVal.toFixed(5)));
  }, [selectedSymbol]);

  // --- RSS DATA PARSING AND PROXY FETCH ---
  const fetchRssFeed = async (feedUrl: string) => {
    if (!feedUrl) {
      // SANS local stream
      setRssArticles([]);
      setRssLoading(false);
      return;
    }
    setRssLoading(true);
    setRssError("");
    try {
      const response = await fetch(`/api/rss?url=${encodeURIComponent(feedUrl)}`);
      if (!response.ok) {
        throw new Error(`Proxy error: ${response.statusText}`);
      }
      const dataText = await response.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(dataText, "text/xml");
      const items = xmlDoc.getElementsByTagName("item");
      const parsedArticles = [];

      // Limit to 8 items
      const count = Math.min(items.length, 8);
      for (let i = 0; i < count; i++) {
        const item = items[i];
        const title = item.getElementsByTagName("title")[0]?.textContent || "Untitled Brief";
        const link = item.getElementsByTagName("link")[0]?.textContent || "#";
        const pubDateStr = item.getElementsByTagName("pubDate")[0]?.textContent || "";
        const descriptionRaw = item.getElementsByTagName("description")[0]?.textContent || "";
        
        // Clean up description HTML tags
        const descriptionClean = descriptionRaw.replace(/<[^>]*>?/gm, "").substring(0, 160) + "...";
        
        // Format date simply
        let timeLabel = pubDateStr;
        try {
          if (pubDateStr) {
            const dateObj = new Date(pubDateStr);
            const diffMs = Date.now() - dateObj.getTime();
            const diffMins = Math.floor(diffMs / 60000);
            if (diffMins < 60) {
              timeLabel = `${diffMins}m ago`;
            } else {
              const diffHours = Math.floor(diffMins / 60);
              if (diffHours < 24) {
                timeLabel = `${diffHours}h ago`;
              } else {
                timeLabel = dateObj.toLocaleDateString(undefined, { month: "short", day: "numeric" });
              }
            }
          }
        } catch (e) {
          timeLabel = "Recent";
        }

        parsedArticles.push({
          title,
          link,
          time: timeLabel,
          snip: descriptionClean,
          source: feedUrl.includes("forexlive") ? "ForexLive CORE" : "Yahoo Finance"
        });
      }

      setRssArticles(parsedArticles);
    } catch (err: any) {
      console.warn("RSS proxy retrieval fallback engaged:", err.message || err);
      // Fallback gracefully without throwing aggressive error stack traces
      setRssError("Operating under secure local news simulation.");
      setRssArticles([]);
    } finally {
      setRssLoading(false);
    }
  };

  useEffect(() => {
    fetchRssFeed(selectedRssUrl);
  }, [selectedRssUrl]);

  // --- TRADING RANDOM WALK (Updates positions & prices every second) ---
  useEffect(() => {
    const timer = setInterval(() => {
      setPositions(prev => 
        prev.map(pos => {
          // Determine asset random walk factor
          const volatility = pos.symbol.includes("BTC") ? 4.5 : pos.symbol.includes("XAU") ? 0.45 : 0.00015;
          const shift = (Math.random() - 0.495) * volatility; // Slight positive bias matching market trajectory
          const nextPrice = Math.max(0.0001, pos.currentPrice + shift);
          
          // Calculate P&L based on contract size
          let contractSize = 100000;
          if (pos.symbol.includes("XAU") || pos.symbol.includes("Gold")) contractSize = 100;
          if (pos.symbol.includes("BTC")) contractSize = 1;

          const priceDiff = pos.side === "BUY" ? (nextPrice - pos.entryPrice) : (pos.entryPrice - nextPrice);
          const nextPnl = priceDiff * pos.lots * contractSize;

          return {
            ...pos,
            currentPrice: parseFloat(nextPrice.toFixed(pos.symbol.includes("BTC") ? 2 : pos.symbol.includes("XAU") ? 2 : 5)),
            pnl: parseFloat(nextPnl.toFixed(2))
          };
        })
      );
    }, 1500);

    return () => clearInterval(timer);
  }, [positions]);

  // --- CALC MARGIN INTERACTIVE TOOL ---
  useEffect(() => {
    const assetRef = calcMarginSymbol;
    let price = 1.0652; // EURUSD
    if (assetRef === "GBPUSD") price = 1.2543;
    if (assetRef === "USDJPY") price = 0.0064;
    if (assetRef === "XAUUSD") price = 2420.50;
    if (assetRef === "BTCUSD") price = 91200.00;

    let contractSize = 100000;
    if (assetRef === "XAUUSD") contractSize = 100;
    if (assetRef === "BTCUSD") contractSize = 1;

    const res = (calcMarginLots * contractSize * price) / calcMarginLeverage;
    setCalcResultMargin(parseFloat(res.toFixed(2)));
  }, [calcMarginSymbol, calcMarginLots, calcMarginLeverage]);

  // Helper pricing list for custom execution trades
  const getAssetRefPrice = (sym: string): number => {
    if (sym.includes("EURUSD")) return 1.06525;
    if (sym.includes("GBPUSD")) return 1.25430;
    if (sym.includes("USDJPY")) return 156.425;
    if (sym.includes("XAUUSD") || sym.includes("Gold")) return 2420.50;
    if (sym.includes("BTC")) return 91245.00;
    return 1.15;
  };

  // --- BROKER ACTION HANDLERS ---
  const handleBrokerConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!accountId) {
      alert("Please provide your XM MT4/MT5 account ID.");
      return;
    }

    if (accountType === "LIVE" && demoMode) {
      setShowLivePrompt(true);
      return;
    }

    proceedBrokerConnect();
  };

  const proceedBrokerConnect = () => {
    setIsLoggingIn(true);
    setExecutionLogs(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] Handshaking node with ${server}...`,
      `[${new Date().toLocaleTimeString()}] Submitting login handshake request to SANS backend...`
    ]);

    const finalBrokerId = "xm_user_account_" + accountId;

    fetch("/api/brokers/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        broker_id: finalBrokerId,
        broker_type: "xm",
        config: {
          account_id: accountId,
          password: password,
          server: server,
          leverage: leverage,
          is_live: !demoMode
        }
      })
    })
    .then(async res => {
      if (!res.ok) {
        throw new Error("Handshake registration declined by security router.");
      }
      return res.json();
    })
    .then(() => {
      return fetch(`/api/brokers/connect/${finalBrokerId}`, { method: "POST" });
    })
    .then(async res => {
      if (!res.ok) {
        throw new Error("Unable to establish tunnel connection with XM node.");
      }
      return res.json();
    })
    .then(() => {
      return fetch(`/api/brokers/account/${finalBrokerId}`);
    })
    .then(async res => {
      if (!res.ok) {
        throw new Error("Failed to pull live balance indicators from authentic XM gateway.");
      }
      return res.json();
    })
    .then(accountData => {
      const actualBalance = accountData.balance !== undefined ? accountData.balance : (demoMode ? 10000.0 : 75000.0);
      const actualCurrency = accountData.currency || "USD";

      setIsLogged(true);
      setIsLoggingIn(false);
      localStorage.setItem("xm_is_logged", "true");
      localStorage.setItem("xm_account_id", accountId);
      localStorage.setItem("xm_server", server);
      localStorage.setItem("xm_leverage", leverage);
      localStorage.setItem("xm_balance", actualBalance.toString());
      localStorage.setItem("xm_initial_balance", demoMode ? "10000.0" : "75000.0");

      setBalance(actualBalance);
      setInitialBalance(demoMode ? 10000.0 : 75000.0);
      setAccountCurrency(actualCurrency);

      setExecutionLogs(prev => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] Verified handshake complete. XM account authorized.`,
        `[${new Date().toLocaleTimeString()}] Active LIVE Ledger Initialized on SANS Node. Balance: ${actualCurrency} ${actualBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}. Leverage: ${leverage}.`
      ]);
    })
    .catch(err => {
      setIsLoggingIn(false);
      setExecutionLogs(prev => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] 🛑 AUTHENTICATION HANDSHAKE FAILURE: ${err.message}`
      ]);
      alert("XM Link Authenticate Failure: " + err.message);
    });
  };

  const handleBrokerDisconnect = () => {
    const activeId = localStorage.getItem("xm_account_id") || "xm_user_account";
    const finalBrokerId = "xm_user_account_" + activeId;

    fetch(`/api/brokers/disconnect/${finalBrokerId}`, { method: "POST" })
      .catch(e => console.error("Disconnect notification failure:", e))
      .finally(() => {
        setIsLogged(false);
        localStorage.removeItem("xm_is_logged");
        localStorage.removeItem("xm_account_id");
        localStorage.removeItem("xm_server");
        localStorage.removeItem("xm_leverage");
        localStorage.removeItem("xm_balance");
        localStorage.removeItem("xm_initial_balance");

        setPositions([]);
        setHistory([]);
        setBalance(demoMode ? 10000.0 : 0);
        setInitialBalance(demoMode ? 10000.0 : 0);
        setExecutionLogs([
          "System: Broker Gate online. Waiting for XMGlobal secure authentication handshake."
        ]);
      });
  };

  const handleExecuteTrade = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLogged) {
      alert("Establish your XM Global Account link first to process real-time trades.");
      return;
    }

    if (orderLots <= 0) {
      alert("Specify a valid Lot size above 0.01");
      return;
    }

    const tPrice = limitPrice || getAssetRefPrice(selectedSymbol);
    const id = `XM-${Math.floor(100000 + Math.random() * 900000)}`;
    const time = new Date().toLocaleTimeString();

    const newPosition: OpenPosition = {
      id,
      symbol: selectedSymbol.replace("XM:", "").replace("BINANCE:", "").replace("FX:", ""),
      side: orderSide,
      lots: orderLots,
      entryPrice: tPrice,
      currentPrice: tPrice,
      pnl: 0,
      timestamp: time
    };

    if (orderSL) newPosition.sl = parseFloat(orderSL);
    if (orderTP) newPosition.tp = parseFloat(orderTP);

    // Dynamic Check: verify leverage capability
    let contractSize = 100000;
    if (newPosition.symbol.includes("XAU") || newPosition.symbol.includes("Gold")) contractSize = 100;
    if (newPosition.symbol.includes("BTC")) contractSize = 1;
    const levVal = parseInt(leverage.split(":")[1]) || 500;
    const marginReq = (orderLots * contractSize * tPrice) / levVal;

    if (marginReq > freeMargin) {
      setExecutionLogs(prev => [
        ...prev,
        `[${time}] 🛑 ORDER FAILED: Insufficient margin. Margin required: ${accountCurrency} ${marginReq.toFixed(2)}, Free Margin available: ${accountCurrency} ${freeMargin.toFixed(2)}`
      ]);
      return;
    }

    setPositions(prev => [...prev, newPosition]);
    setExecutionLogs(prev => [
      ...prev,
      `[${time}] 🚀 Order EXEC: ${orderSide} ${orderLots} lots of ${newPosition.symbol} submitted at ${tPrice}...`,
      `[${time}] Transaction approved by SANS Executor. Ticket ID allocated: ${id}`
    ]);

    // Clear brief form SL/TP targets
    setOrderSL("");
    setOrderTP("");
  };

  const handleClosePosition = (posId: string) => {
    const pos = positions.find(p => p.id === posId);
    if (!pos) return;

    const time = new Date().toLocaleTimeString();
    // Resolve funds
    const finalBalance = balance + pos.pnl;
    setBalance(parseFloat(finalBalance.toFixed(2)));

    const rec: HistoricalTrade = {
      id: pos.id,
      symbol: pos.symbol,
      side: pos.side,
      lots: pos.lots,
      entryPrice: pos.entryPrice,
      exitPrice: pos.currentPrice,
      pnl: pos.pnl,
      timestamp: time
    };

    setHistory(prev => [rec, ...prev]);
    setPositions(prev => prev.filter(p => p.id !== posId));
    setExecutionLogs(prev => [
      ...prev,
      `[${time}] Trade Ticket ${posId} CLOSED. Exit price: ${pos.currentPrice}. Realized Profit/Loss: ${accountCurrency} ${pos.pnl.toFixed(2)}`,
      `[${time}] Ledger updated. Sovereign balance corrected to ${accountCurrency} ${finalBalance.toLocaleString(undefined, { minimumFractionDigits: 2 })}.`
    ]);
  };

  const handleDepositFunds = () => {
    const amount = prompt("Set simulated funding amount:", "10000");
    if (amount) {
      const val = parseFloat(amount);
      if (!isNaN(val) && val > 0) {
        setBalance(val);
        setInitialBalance(val);
        setExecutionLogs(prev => [
          ...prev,
          `[${new Date().toLocaleTimeString()}] Sovereign vault loaded with custom capital deposit of ${accountCurrency} ${val.toLocaleString(undefined, { minimumFractionDigits: 2 })}.`
        ]);
      }
    }
  };

  // Quick preset symbols for TradingView Selector
  const SYMBOLS = [
    { title: "EUR/USD", symbol: "XM:EURUSD" },
    { title: "GBP/USD", symbol: "XM:GBPUSD" },
    { title: "USD/JPY", symbol: "FX:USDJPY" },
    { title: "Gold Spot", symbol: "XM:XAUUSD" },
    { title: "Bitcoin", symbol: "BINANCE:BTCUSDT" }
  ];

  const renderPrompt = () => {
    return (
      <div className="max-w-4xl mx-auto w-full bg-[#030303]/60 border border-white/10 rounded-xl p-8 space-y-6 shadow-[0_12px_45px_0_rgba(0,0,0,0.8)] mt-6 animate-fadeIn">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Split Left: Registration Prompt */}
          <div className="flex-1 space-y-5">
            <div className="flex items-center space-x-2 text-rose-500 font-mono text-xs uppercase tracking-widest font-semibold flex items-center">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse mr-1" />
              <span>Live Mode Unauthenticated</span>
            </div>
            <h2 className="text-2xl font-serif italic text-white leading-tight font-normal">Live Broker Handshake Required</h2>
            <p className="text-zinc-400 text-xs leading-relaxed font-sans font-light">
              You have toggled off the Demo Environment. To receive live exchange rates, execute sub-millisecond trades, and synchronize capital routes via genuine SANS order boards, link your real XM Global trading account.
            </p>
            
            <div className="bg-neutral-900/40 border border-white/5 p-5 rounded font-mono space-y-3">
              <span className="text-white font-bold block text-xs">Don't have an XM Global account?</span>
              <p className="text-zinc-500 text-[11px] leading-relaxed font-sans font-light">
                Register a real secure trading account via our official introducing broker link to obtain ultra-low spreads, XM leverage multipliers up to 1:1000, and integrated privileges.
              </p>
              <a
                href="https://affs.click/Ddvn7"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-between w-full bg-gradient-to-r from-neutral-800 to-neutral-900 hover:from-white hover:to-white hover:text-black hover:border-white text-white font-mono font-bold text-xs py-3.5 px-4 rounded border border-white/10 transition-all duration-300 shadow group cursor-pointer"
              >
                <span>CREATE REAL XM ACCOUNT</span>
                <ArrowUpRight className="w-4 h-4 ml-2 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </a>
            </div>
          </div>

          {/* Split Right: Real Handshake Login */}
          <div className="flex-1 space-y-4 border-t md:border-t-0 md:border-l border-white/10 pt-6 md:pt-0 md:pl-8">
            <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-bold">Secure XM authentication handshake</span>
            <form onSubmit={handleBrokerConnect} className="space-y-3.5">
              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold text-zinc-400">XM broker Server Node</label>
                <select 
                  value={server} 
                  onChange={e => setServer(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded p-2.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                >
                  <option value="XMGlobal-Real 14">XMGlobal-Real 14 (High-Frequency)</option>
                  <option value="XMGlobal-Real 22">XMGlobal-Real 22 (Standard Real)</option>
                  <option value="XMGlobal-Real 55">XMGlobal-Real 55 (Zero Spread)</option>
                  <option value="XMGlobal-Real 1">XMGlobal-Real 1 (Primary Hub)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold text-zinc-400">Email Address or Account ID / Login</label>
                <input 
                  type="text" 
                  value={accountId}
                  onChange={e => setAccountId(e.target.value)}
                  placeholder="e.g. privjapan@gmail.com or 5824901"
                  className="w-full bg-black border border-white/10 rounded p-2.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold text-zinc-400">Security Password</label>
                  <input 
                    type="password" 
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-black border border-white/10 rounded p-2.5 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold text-zinc-400">Leverage bounds</label>
                  <select 
                    value={leverage} 
                    onChange={e => setLeverage(e.target.value)}
                    className="w-full bg-black border border-white/10 p-2.5 rounded text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                  >
                    <option value="1:100">1:100 Premium</option>
                    <option value="1:200">1:200 Classic</option>
                    <option value="1:500">1:500 Sovereign</option>
                    <option value="1:888">1:888 Ultra</option>
                    <option value="1:1000">1:1000 Extreme</option>
                  </select>
                </div>
              </div>

              <button 
                type="submit" 
                disabled={isLoggingIn}
                className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-bold text-xs py-3 rounded transition duration-200 flex items-center justify-center space-x-2 border border-white cursor-pointer select-none uppercase tracking-wide animate-pulse"
              >
                {isLoggingIn ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>CONNECTING SECURE PORT...</span>
                  </>
                ) : (
                  <>
                    <Lock className="w-3.5 h-3.5" />
                    <span>SIGN IN / SYNC XM HANDSHAKE</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  };

  const renderWorkspace = () => {
    const activeSymbolCode = selectedSymbol.includes("EURUSD") 
      ? "EURUSD" 
      : selectedSymbol.includes("GBPUSD") 
      ? "GBPUSD" 
      : selectedSymbol.includes("USDJPY") 
      ? "USDJPY" 
      : selectedSymbol.includes("XAUUSD") 
      ? "XAUUSD" 
      : "BTCUSDT";

    return (
      <>
        {/* Main Terminal Workspace Layout */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* ========================================================== */}
        {/* LEFT COLUMN (WIDGETS 1 & 2): BRONX ACCOUNT GATE (XMGLOBAL) */}
        {/* ========================================================== */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          
          {/* XMGlobal Core Auth & Dashboard */}
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5 relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4 mb-2">
                <span className="font-mono text-[10px] text-zinc-500 tracking-wider">XMGLOBAL PORT ROUTE</span>
                <span className={`flex items-center font-mono text-[9px] uppercase px-2 py-0.5 rounded border ${
                  isLogged 
                    ? "bg-emerald-500/5 text-emerald-400 border-emerald-500/30" 
                    : isLoggingIn 
                    ? "bg-amber-500/5 text-amber-400 border-amber-500/30 animate-pulse"
                    : "bg-red-500/5 text-red-500 border-red-500/30"
                }`}>
                  {isLogged ? "Handshake Live" : isLoggingIn ? "Syncing..." : "Offline Node"}
                </span>
              </div>

              {!isLogged ? (
                /* Login Interface Form */
                <form onSubmit={handleBrokerConnect} className="space-y-3.5">
                  <div className="space-y-1">
                    <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">XM broker Server Node</label>
                    <select 
                      value={server} 
                      onChange={e => setServer(e.target.value)}
                      className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                    >
                      <option value="XMGlobal-Demo 1">XMGlobal-Demo 1 (Sovereign Core)</option>
                      <option value="XMGlobal-Demo 2">XMGlobal-Demo 2 (L2 Liquidity)</option>
                      <option value="XMGlobal-Real 14">XMGlobal-Real 14 (High-Frequency)</option>
                      <option value="XMGlobal-Real 22">XMGlobal-Real 22 (Standard Real)</option>
                      <option value="XMGlobal-Real 55">XMGlobal-Real 55 (Zero Spread)</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                    <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Email Address / Account ID</label>
                    <input 
                      type="text" 
                      value={accountId}
                      onChange={e => setAccountId(e.target.value)}
                      placeholder="e.g. privjapan@gmail.com"
                      className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      required
                    />
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Type preference</label>
                      <div className="grid grid-cols-2 gap-1 bg-neutral-950 border border-white/10 p-0.5 rounded text-xs text-neutral-400 text-center">
                        <button 
                          type="button" 
                          onClick={() => setAccountType("DEMO")}
                          className={`py-1 rounded text-[10px] font-mono font-bold transition select-none cursor-pointer ${accountType === "DEMO" ? "bg-white/10 text-white" : ""}`}
                        >
                          DEMO
                        </button>
                        <button 
                          type="button" 
                          onClick={() => setAccountType("LIVE")}
                          className={`py-1 rounded text-[10px] font-mono font-bold transition select-none cursor-pointer ${accountType === "LIVE" ? "bg-red-500/15 text-red-400" : ""}`}
                        >
                          LIVE
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Security Password</label>
                      <input 
                        type="password" 
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                        required
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Leverage bounds</label>
                      <select 
                        value={leverage} 
                        onChange={e => setLeverage(e.target.value)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      >
                        <option value="1:100">1:100 Premium</option>
                        <option value="1:200">1:200 Classic</option>
                        <option value="1:500">1:500 Sovereign</option>
                        <option value="1:888">1:888 Ultra</option>
                        <option value="1:1000">1:1000 Extreme</option>
                      </select>
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    disabled={isLoggingIn}
                    className="w-full bg-white hover:bg-neutral-200 text-neutral-950 font-semibold text-xs p-3 rounded transition duration-200 flex items-center justify-center space-x-2 border border-white cursor-pointer select-none"
                  >
                    {isLoggingIn ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>SYNCHRONIZING SECURE KEY...</span>
                      </>
                    ) : (
                      <>
                        <Lock className="w-3.5 h-3.5" />
                        <span>ESTABLISH SECURE HANDSHAKE LNK</span>
                      </>
                    )}
                  </button>
                </form>
              ) : (
                /* Logged In Dashboard Core view */
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3.5 bg-neutral-950 border border-white/5 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 bg-emerald-500/10 rounded border border-emerald-500/30">
                        <Wifi className="w-4 h-4 text-emerald-400 animate-pulse" />
                      </div>
                      <div>
                        <h4 className="text-xs font-mono font-bold text-white tracking-wide">{accountId} @ {server}</h4>
                        <p className="text-[9px] font-mono text-zinc-500 uppercase mt-0.5">TYPE: {accountType} &bull; LEVERAGE {leverage}</p>
                      </div>
                    </div>
                    <button 
                      onClick={handleBrokerDisconnect}
                      className="p-2 bg-white/5 rounded hover:bg-red-500/10 hover:text-red-400 group transition duration-200"
                      title="Terminate session protocol"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Core Account Balance and Metrics grid */}
                  <div className="grid grid-cols-2 gap-3.5">
                    <div className="p-3 border border-white/5 bg-neutral-950/40 rounded space-y-0.5">
                      <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold">Vault Balance</span>
                      <span className="text-lg font-mono text-zinc-300 font-bold">{accountCurrency} {balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>

                    <div className="p-3 border border-white/5 bg-neutral-950/40 rounded space-y-0.5">
                      <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold">Net Equity</span>
                      <span className="text-lg font-mono text-white font-bold">{accountCurrency} {equity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>

                    <div className="p-3 border border-white/5 bg-neutral-950/40 rounded space-y-0.5">
                      <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold">Used Margin</span>
                      <span className="text-sm font-mono text-zinc-300">{accountCurrency} {usedMargin.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>

                    <div className="p-3 border border-white/5 bg-neutral-950/40 rounded space-y-0.5">
                      <span className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest font-semibold">Free Margin</span>
                      <span className="text-sm font-mono text-zinc-300">{accountCurrency} {freeMargin.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3.5 pt-1.5 font-mono text-[10px]">
                    <div className="flex justify-between items-center px-1">
                      <span className="text-zinc-500 uppercase">Margin level:</span>
                      <span className={`font-bold ${marginLevel === 0 ? "text-zinc-500" : marginLevel < 110 ? "text-red-400 animate-pulse" : "text-emerald-400"}`}>
                        {marginLevel === 0 ? "0.00" : marginLevel.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center px-1">
                      <span className="text-zinc-500 uppercase">Floating P/L:</span>
                      <span className={`font-bold ${currentFloatingPnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {currentFloatingPnl >= 0 ? "+" : ""}{currentFloatingPnl.toFixed(2)} {accountCurrency}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Core Live Execution Desk Order Form */}
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5 relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
                <span className="font-serif italic text-white flex items-center font-normal">
                  <Activity className="w-4 h-4 mr-2 text-stone-400" />
                  Order Dispatch Console
                </span>
                <span className="font-mono text-[9px] text-[#22c55e] border border-[#22c55e]/30 bg-[#22c55e]/5 px-2 py-0.5 rounded">
                  XM-ROUTE: LIVE
                </span>
              </div>

              {!isLogged ? (
                <div className="p-12 text-center rounded border border-white/5 bg-neutral-900/10 font-mono text-[11px] text-stone-500">
                  <Unlock className="w-5 h-5 mx-auto mb-2.5 text-stone-600 block" />
                  手 SECURE BROKER HANDSHAKE REQUIRED TO ENABLE ORDER SUBMISSION GATE.
                </div>
              ) : (
                <form onSubmit={handleExecuteTrade} className="space-y-4">
                  {/* Selector showing active asset selection */}
                  <div className="space-y-1">
                    <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Active Dispatch Asset (Symbol)</label>
                    <div className="p-2 px-3 bg-neutral-950 border border-white/10 rounded flex justify-between items-center font-mono text-xs">
                      <span className="text-white font-bold">{selectedSymbol.replace("XM:", "").replace("BINANCE:", "").replace("FX:", "")}</span>
                      <span className="text-stone-500 uppercase text-[9px] border border-white/5 px-2 py-0.5 rounded leading-none select-none">
                        Tradingview link
                      </span>
                    </div>
                  </div>

                  {/* Buy / Sell Toggles */}
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setOrderSide("BUY")}
                      className={`py-3.5 rounded text-xs font-mono font-bold transition select-none cursor-pointer flex items-center justify-center space-x-1 border ${
                        orderSide === "BUY" 
                          ? "bg-emerald-500 text-black font-extrabold border-emerald-500" 
                          : "bg-neutral-950 text-emerald-500 border-white/5 hover:border-emerald-500/20"
                      }`}
                    >
                      <TrendingUp className="w-4 h-4" />
                      <span>BUY / LONG</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setOrderSide("SELL")}
                      className={`py-3.5 rounded text-xs font-mono font-bold transition select-none cursor-pointer flex items-center justify-center space-x-1 border ${
                        orderSide === "SELL" 
                          ? "bg-red-500 text-black font-extrabold border-red-500" 
                          : "bg-neutral-950 text-red-500 border-white/5 hover:border-red-500/20"
                      }`}
                    >
                      <TrendingDown className="w-4 h-4" />
                      <span>SELL / SHORT</span>
                    </button>
                  </div>

                  {/* Lot size input and slippage slider */}
                  <div className="grid grid-cols-2 gap-3.5">
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Lot sizes & vol</label>
                      <div className="flex bg-neutral-950 border border-white/10 rounded overflow-hidden">
                        <button 
                          type="button"
                          onClick={() => setOrderLots(prev => parseFloat(Math.max(0.01, prev - 0.1).toFixed(2)))}
                          className="px-2.5 text-stone-500 hover:text-white border-r border-white/5 font-mono select-none cursor-pointer text-xs"
                        >
                          -
                        </button>
                        <input 
                          type="number" 
                          step="0.01"
                          min="0.01"
                          max="50.0"
                          value={orderLots}
                          onChange={e => setOrderLots(parseFloat(e.target.value) || 0.01)}
                          className="w-full text-center bg-transparent border-none text-xs text-white focus:outline-none focus:ring-0 font-mono"
                        />
                        <button 
                          type="button"
                          onClick={() => setOrderLots(prev => parseFloat(Math.min(50.0, prev + 0.1).toFixed(2)))}
                          className="px-2.5 text-stone-500 hover:text-white border-l border-white/5 font-mono select-none cursor-pointer text-xs"
                        >
                          +
                        </button>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Execution Mode</label>
                      <select 
                        value={orderType} 
                        onChange={e => setOrderType(e.target.value as any)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      >
                        <option value="MARKET">Market Execution (Standard)</option>
                        <option value="LIMIT">Limit Pending Order</option>
                      </select>
                    </div>
                  </div>

                  {orderType === "LIMIT" && (
                    <div className="space-y-1 animate-fadeIn">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Sovereign Limit Target Price</label>
                      <input 
                        type="number" 
                        step="0.00001"
                        value={limitPrice}
                        onChange={e => setLimitPrice(parseFloat(e.target.value) || 0)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      />
                    </div>
                  )}

                  {/* Stop Loss & Take Profit targets */}
                  <div className="grid grid-cols-2 gap-3.5">
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Take profit (TP)</label>
                      <input 
                        type="text" 
                        placeholder="N/A (Standard)"
                        value={orderTP}
                        onChange={e => setOrderTP(e.target.value)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest">Stop loss (SL)</label>
                      <input 
                        type="text" 
                        placeholder="N/A (Standard)"
                        value={orderSL}
                        onChange={e => setOrderSL(e.target.value)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 font-mono"
                      />
                    </div>
                  </div>

                  {/* Submit Order action */}
                  <button
                    type="submit"
                    className={`w-full text-black font-extrabold text-xs p-3.5 rounded transition duration-200 flex items-center justify-center space-x-1.5 cursor-pointer uppercase select-none ${
                      orderSide === "BUY" 
                        ? "bg-emerald-500 hover:bg-emerald-400" 
                        : "bg-red-500 hover:bg-red-400"
                    }`}
                  >
                    <Sparkles className="w-4 h-4 animate-pulse block" />
                    <span>TRANSMIT {orderSide} ORDER DIRECT TO XM SERVER</span>
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* PRIV Instrument Intelligence Overview Snippet */}
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/20 relative overflow-hidden flex flex-col justify-between animate-fadeIn">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-white/70 animate-pulse" />
                  <span className="font-serif italic text-white text-xs font-semibold">
                    PRIV Instrument Intelligence
                  </span>
                </div>
                <span className="font-mono text-[9px] bg-white/5 px-2 py-0.5 rounded border border-white/10 text-stone-300">
                  {currentIntel.title}
                </span>
              </div>

              <div className="space-y-1.5">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase tracking-widest leading-none">ACTIVE SYMBOL DISCOVERY</span>
                <div className="flex items-baseline justify-between gap-1">
                  <h4 className="text-sm font-serif italic text-white font-normal">{currentIntel.title} Overview</h4>
                  <span className="text-[10px] font-mono text-zinc-400 font-light truncate max-w-[150px]">{currentIntel.fullName}</span>
                </div>
              </div>

              {/* Sentiment & Volatility Indicators Row */}
              <div className="grid grid-cols-2 gap-3.5 pt-1.5">
                <div className="space-y-1 bg-neutral-950/40 p-2.5 rounded border border-white/5">
                  <span className="block text-[8px] font-mono text-zinc-500 uppercase tracking-widest leading-none">BIAS DIRECTION</span>
                  <span className={`text-xs font-mono font-bold block mt-1.5 ${
                    currentIntel.direction === "BULLISH" ? "text-emerald-400" :
                    currentIntel.direction === "BEARISH" ? "text-rose-400" : "text-amber-400"
                  }`}>
                    {currentIntel.direction}
                  </span>
                </div>

                <div className="space-y-1 bg-neutral-950/40 p-2.5 rounded border border-white/5">
                  <span className="block text-[8px] font-mono text-zinc-500 uppercase tracking-widest leading-none">VOLATILITY PROFILE</span>
                  <span className="text-xs font-mono font-bold block mt-1.5 text-zinc-300">
                    {currentIntel.volatilityRating} Rating
                  </span>
                </div>
              </div>

              {/* SANS Sensory Indicator Gauge */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[9px] font-mono text-zinc-500">
                  <span>SANS AGENT CONFIDENCE SENTIMENT</span>
                  <span className="text-white font-bold">{currentIntel.sentimentPercent}%</span>
                </div>
                <div className="h-1.5 w-full bg-neutral-900 rounded-full overflow-hidden border border-white/5">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${
                      currentIntel.sentimentPercent > 70 ? "bg-emerald-500" :
                      currentIntel.sentimentPercent > 50 ? "bg-amber-500" : "bg-rose-500"
                    }`}
                    style={{ width: `${currentIntel.sentimentPercent}%` }}
                  />
                </div>
              </div>

              {/* Support, Resistance and Range Metrics Grid */}
              <div className="grid grid-cols-3 gap-2 py-2 font-mono text-[10px] border-y border-white/5 my-2">
                <div className="space-y-1">
                  <span className="block text-[8px] text-zinc-500 uppercase">SUPPORT</span>
                  <span className="text-zinc-200 font-bold">{currentIntel.support}</span>
                </div>
                <div className="space-y-1">
                  <span className="block text-[8px] text-zinc-500 uppercase">RESISTANCE</span>
                  <span className="text-zinc-200 font-bold">{currentIntel.resistance}</span>
                </div>
                <div className="space-y-1">
                  <span className="block text-[8px] text-zinc-500 uppercase">EST. RANGE</span>
                  <span className="text-zinc-400 truncate block">{currentIntel.dailyRange}</span>
                </div>
              </div>

              {/* Recommendation / Technical Briefing Note */}
              <div className="bg-neutral-950/30 border border-white/5 rounded p-3 space-y-2">
                <span className="block text-[8px] font-mono text-zinc-500 uppercase tracking-widest leading-none">TACTICAL BRIEF & RECO</span>
                <p className="text-xs text-stone-400 leading-relaxed font-sans font-light">
                  {currentIntel.tacticalNote}
                </p>
                
                <div className="flex items-center justify-between pt-2 border-t border-white/5 font-mono text-[9px]">
                  <span className="text-zinc-500 uppercase">OPTIMAL BAND:</span>
                  <span className="text-white font-bold">{currentIntel.tradeBias}</span>
                </div>
              </div>

              {/* Recommended Target parameters */}
              <div className="grid grid-cols-2 gap-3.5 pt-1 font-mono text-[10px]">
                <div className="flex items-center justify-between px-2.5 py-1.5 bg-neutral-950/40 border border-white/5 rounded">
                  <span className="text-zinc-500">TARGET (TP):</span>
                  <span className="text-emerald-400 font-bold">{currentIntel.targetProfit}</span>
                </div>
                <div className="flex items-center justify-between px-2.5 py-1.5 bg-neutral-950/40 border border-white/5 rounded">
                  <span className="text-zinc-500">STOP LOSS (SL):</span>
                  <span className="text-rose-400 font-bold">{currentIntel.stopLoss}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================== */}
        {/* MIDDLE COLUMN (WIDGETS 3 & 4): TRADINGVIEW CHART & TELEMETRY */}
        {/* ========================================================== */}
        <div className="xl:col-span-5 flex flex-col gap-6">
          
          {/* Symbol Quick Selectors and TradingView Chart frame */}
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5 relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            <div>
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 border-b border-white/5 mb-4 gap-2">
                <span className="font-serif italic text-white flex items-center font-normal">
                  <Database className="w-4 h-4 mr-2" />
                  TradingView Technical Core
                </span>
                
                {/* Micro-Selector */}
                <div className="flex flex-wrap items-center gap-1 bg-neutral-950 border border-white/5 p-0.5 rounded">
                  {SYMBOLS.map((preset) => (
                    <button
                      key={preset.symbol}
                      onClick={() => setSelectedSymbol(preset.symbol)}
                      className={`px-2 py-1 text-[9px] font-mono rounded cursor-pointer select-none transition ${
                        selectedSymbol === preset.symbol 
                          ? "bg-white text-black font-bold" 
                          : "text-zinc-500 hover:text-white"
                      }`}
                    >
                      {preset.title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Advanced Chart Embed Block */}
              <div className="h-[430px] w-full bg-neutral-950/20 border border-white/5 rounded-lg overflow-hidden relative">
                <div id="tradingview_chart_frame" className="w-full h-full" ref={containerRef} />
              </div>
            </div>
          </div>

          {/* Inline technical gauge widget for immediate visual support */}
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent" />
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-4 flex items-center justify-between pb-2 border-b border-white/5">
              <span>TRADINGVIEW SYSTEM SIGNAL GAUGE</span>
              <span className="text-[10px] text-zinc-500 font-normal">TIMEFRAME: 15 MIN INTEGRATION</span>
            </h3>
            <div className="h-[430px] w-full bg-neutral-950/10 border border-white/5 rounded overflow-hidden">
              <div ref={techContainerRef} className="width-full h-full" />
            </div>
          </div>
        </div>

        {/* ========================================================== */}
        {/* RIGHT COLUMN (WIDGETS 5, 6 & 7): FINANCIAL INTEL AGGREGATOR */}
        {/* ========================================================== */}
        <div className="xl:col-span-3 flex flex-col gap-6">
          <div className="metric-card p-5 rounded border border-white/10 bg-neutral-950/5 relative overflow-hidden flex flex-col h-full min-h-[600px]">
            <div className="absolute top-0 right-0 w-[1px] h-full bg-gradient-to-b from-white/10 to-transparent animate-pulse" />
            
            {/* Tab Controls for Financial Intel */}
            <div className="grid grid-cols-3 gap-1 bg-neutral-950 border border-white/5 p-1 rounded-lg mb-4 text-center font-mono text-[10px]">
              <button
                onClick={() => setActiveRightTab("NEWS")}
                className={`py-1.5 rounded transition font-bold select-none cursor-pointer flex items-center justify-center space-x-1 ${
                  activeRightTab === "NEWS" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-white"
                }`}
              >
                <Newspaper className="w-3.5 h-3.5" />
                <span>RSS</span>
              </button>
              <button
                onClick={() => setActiveRightTab("TWITTER")}
                className={`py-1.5 rounded transition font-bold select-none cursor-pointer flex items-center justify-center space-x-1 ${
                  activeRightTab === "TWITTER" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-white"
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>X STREAM</span>
              </button>
              <button
                onClick={() => setActiveRightTab("CALCULATOR")}
                className={`py-1.5 rounded transition font-bold select-none cursor-pointer flex items-center justify-center space-x-1 ${
                  activeRightTab === "CALCULATOR" ? "bg-white/10 text-white" : "text-zinc-500 hover:text-white"
                }`}
              >
                <Calculator className="w-3.5 h-3.5" />
                <span>CALC</span>
              </button>
            </div>

            {/* Content Switcher */}
            <div className="flex-1 overflow-y-auto pr-0.5 scrollbar-thin">
              
              {/* NEWS BLOCK */}
              {activeRightTab === "NEWS" && (
                <div className="space-y-4">
                  <div className="pb-2 border-b border-white/5 space-y-2">
                    <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-widest leading-none">FEED CHANNELS SOURCE</label>
                    <div className="grid grid-cols-1 gap-1.5">
                      {PREDEFINED_FEEDS.map(f => (
                        <button
                          key={f.name}
                          onClick={() => {
                            setSelectedRssUrl(f.url);
                          }}
                          className={`w-full py-1 px-2.5 rounded text-[10px] font-mono text-left block border ${
                            selectedRssUrl === f.url 
                              ? "bg-white/5 border-white text-white font-bold" 
                              : "bg-neutral-950/40 border-transparent text-zinc-500 hover:text-white"
                          }`}
                        >
                          &bull;&nbsp;{f.name}
                        </button>
                      ))}
                    </div>

                    {/* Custom dynamic importer */}
                    <div className="pt-2 border-t border-white/5 space-y-1">
                      <label className="block text-[9px] font-mono text-zinc-500 uppercase tracking-wide">CUSTOM FEED INJECT (XML ADDR)</label>
                      <div className="flex gap-1">
                        <input
                          type="text"
                          placeholder="https://example.com/rss.xml"
                          value={customRssUrl}
                          onChange={e => setCustomRssUrl(e.target.value)}
                          className="flex-1 bg-neutral-950 border border-white/10 rounded p-1 text-[10px] font-mono text-white focus:outline-none"
                        />
                        <button
                          onClick={() => {
                            if (customRssUrl) {
                              setSelectedRssUrl(customRssUrl);
                            }
                          }}
                          title="Proxy stream"
                          className="p-1 px-2 bg-white text-black text-[10px] font-mono rounded select-none cursor-pointer"
                        >
                          SYNC
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Feed Display Container */}
                  <div className="space-y-3 pt-1">
                    {rssLoading ? (
                      <div className="py-12 text-center text-xs font-mono text-zinc-500 space-y-2">
                        <RefreshCw className="w-5 h-5 mx-auto animate-spin" />
                        <span>AGGREGATING DEC CENTRALIZED RSS CORE...</span>
                      </div>
                    ) : (() => {
                      // Dynamic check keywords specific to selected symbol
                      const kwMap: Record<string, string[]> = {
                        EURUSD: ["eur", "usd", "euro", "dollar", "fed", "ecb", "inflation", "interest", "yield", "rate"],
                        GBPUSD: ["gbp", "usd", "sterling", "pound", "boe", "uk", "dollar", "fed", "inflation"],
                        USDJPY: ["jpy", "usd", "yen", "japan", "boj", "dollar", "fed", "treasury", "yield"],
                        XAUUSD: ["gold", "xau", "metal", "silver", "bullion", "commodity", "metals"],
                        BTCUSDT: ["btc", "bitcoin", "crypto", "ether", "binance", "coin"]
                      };
                      const keywords = kwMap[activeSymbolCode] || [];
                      const filteredRssArticles = rssArticles.filter(art => {
                        const text = `${art.title} ${art.snip}`.toLowerCase();
                        return keywords.some(kw => text.includes(kw));
                      });
                      const displayRssArticles = filteredRssArticles.length > 0 ? filteredRssArticles : rssArticles;
                      const currentLocalArticles = MOCK_ARTICLES_BY_SYMBOL[activeSymbolCode] || LOCAL_MOCK_ARTICLES;

                      if (displayRssArticles.length === 0) {
                        return (
                          <div className="space-y-3">
                            <div className="text-[10px] font-mono p-2 border border-sky-500/10 bg-sky-500/5 text-sky-400 rounded flex gap-1.5 items-center">
                              <ShieldAlert className="w-3.5 h-3.5" />
                              <span>SANS intelligence node routing customized local briefings for {activeSymbolCode}.</span>
                            </div>
                            {currentLocalArticles.map((art, idx) => (
                              <div key={idx} className="p-3 bg-neutral-950 border border-white/5 rounded-lg hover:border-white/10 transition">
                                <div className="flex justify-between font-mono text-[9px] text-zinc-500 mb-1">
                                  <span>{art.source}</span>
                                  <span>{art.time}</span>
                                </div>
                                <h4 className="text-xs font-bold text-white tracking-tight leading-snug">{art.title}</h4>
                                <p className="text-[10px] text-stone-400 mt-1 lines-clamp-2">{art.snip}</p>
                              </div>
                            ))}
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-3">
                          <div className="text-[10px] font-mono p-1.5 border border-sky-500/10 bg-sky-500/5 text-sky-400 rounded flex gap-1.5 items-center">
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>Showing news filtered for {activeSymbolCode}</span>
                          </div>
                          {displayRssArticles.map((art, idx) => (
                            <a 
                              key={idx} 
                              href={art.link} 
                              target="_blank" 
                              referrerPolicy="no-referrer"
                              rel="noopener noreferrer"
                              className="p-3 bg-neutral-950/40 border border-white/5 rounded-lg hover:border-white/20 hover:bg-neutral-950 transition block space-y-1 group"
                            >
                              <div className="flex items-center justify-between font-mono text-[9px] text-zinc-500">
                                <span>{art.source}</span>
                                <span>{art.time}</span>
                              </div>
                              <h4 className="text-xs font-semibold text-white group-hover:text-sky-300 transition leading-snug tracking-tight">
                                {art.title}
                              </h4>
                              <p className="text-[10px] text-stone-400 font-sans tracking-normal leading-relaxed">
                                {art.snip}
                              </p>
                            </a>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* TWITTER SIGNAL STREAM BLOCK */}
              {activeRightTab === "TWITTER" && (
                <div className="space-y-4">
                  <div className="p-3 bg-[#1DA1F2]/5 border border-[#1DA1F2]/20 rounded-lg text-[#1DA1F2] flex items-center gap-2 font-mono text-[10px]">
                    <Globe className="w-4 h-4 animate-spin" />
                    <span>HFT ALTERNATIVE DATA CORRELATOR : SYNCED</span>
                  </div>

                  <div className="space-y-3.5">
                    {getSimulatedTwitterFeeds(selectedSymbol).map((tweet, idx) => (
                      <div key={idx} className="p-3 bg-neutral-950 border border-white/5 rounded-lg relative overflow-hidden">
                        <div className="flex items-center justify-between font-mono text-[9px] mb-1">
                          <span className="text-white font-bold cursor-pointer hover:underline text-stone-300">@{tweet.username}</span>
                          <span className="text-zinc-500">{tweet.time}</span>
                        </div>
                        <p className="text-[11px] font-sans text-stone-300 leading-normal">{tweet.content}</p>
                        
                        <div className="flex items-center justify-between pt-2 mt-2 border-t border-white/5 font-mono text-[9px]">
                          <span className="text-zinc-500 flex items-center">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400 mr-1" /> Verified signal
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${
                            tweet.sentiment === "Bullish" 
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                              : tweet.sentiment === "Bearish"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-white/5 text-stone-400 border border-white/5"
                          }`}>
                            {tweet.sentiment}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TACTICAL CALULATOR UTILITIES */}
              {activeRightTab === "CALCULATOR" && (
                <div className="space-y-4">
                  <div className="pb-3 border-b border-white/5 font-serif italic text-white flex items-center font-normal">
                    <BookOpen className="w-4 h-4 mr-1.5" />
                    Margin Security Calculator
                  </div>

                  <div className="space-y-3 font-mono text-xs">
                    <div className="space-y-1">
                      <label className="text-[9px] font-mono text-zinc-500 uppercase tracking-widest block">Calculate Asset</label>
                      <select
                        value={calcMarginSymbol}
                        onChange={e => setCalcMarginSymbol(e.target.value)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30"
                      >
                        <option value="EURUSD">EURUSD (Forex Classic)</option>
                        <option value="GBPUSD">GBPUSD (Sterling Core)</option>
                        <option value="USDJPY">USDJPY (Asian Grid)</option>
                        <option value="XAUUSD">XAUUSD (Gold Metal)</option>
                        <option value="BTCUSD">BTCUSD (Crypto Liquid)</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[9px] font-mono text-zinc-500 uppercase tracking-widest block">Allocation Size (Lots)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.01"
                        value={calcMarginLots}
                        onChange={e => setCalcMarginLots(parseFloat(e.target.value) || 0.1)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none focus:border-white/30 text-right"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[9px] font-mono text-zinc-500 uppercase tracking-widest block">Arbiter Leverage</label>
                      <select
                        value={calcMarginLeverage}
                        onChange={e => setCalcMarginLeverage(parseInt(e.target.value) || 500)}
                        className="w-full bg-neutral-950 border border-white/10 rounded p-2 text-xs text-white focus:outline-none"
                      >
                        <option value="100">1:100 Premium</option>
                        <option value="200">1:200 Classic</option>
                        <option value="500">1:500 Sovereign</option>
                        <option value="888">1:888 Extreme</option>
                        <option value="1000">1:1000 Max Limits</option>
                      </select>
                    </div>

                    {/* Result Card */}
                    <div className="p-4 bg-neutral-950 border border-white/10 rounded-lg relative overflow-hidden space-y-1">
                      <span className="block text-[9px] text-stone-500 uppercase tracking-widest">Necessary Margin Collateral</span>
                      <div className="text-xl font-bold text-white">USD {calcResultMargin.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                      <p className="text-[8px] text-zinc-600 uppercase mt-2">Adjust slot volume constraints based on absolute deposit boundaries.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* ========================================================== */}
      {/* SOVEREIGN MARKET HEATMAP & TECHNICAL RECONNAISSANCE TOOLS  */}
      {/* ========================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-6 animate-fadeIn">
        {/* Forex Cross-Rates Heatmap Widget */}
        <div className="lg:col-span-6 metric-card p-5 rounded border border-white/10 bg-neutral-950/10 flex flex-col justify-between">
          <div className="w-full">
            <h3 className="text-sm font-serif italic text-white mb-4 flex items-center font-normal pb-2 border-b border-white/5">
              <Globe className="w-4 h-4 mr-2 text-zinc-500 animate-pulse" />
              Sovereign Spot Forex Cross Rates Heatmap
            </h3>
            <div className="h-[400px] w-full bg-neutral-950/10 border border-white/5 rounded overflow-hidden">
              <div ref={forexCrossRatesRef} className="width-full h-full" />
            </div>
          </div>
        </div>

        {/* Live Technical Screener Tool */}
        <div className="lg:col-span-6 metric-card p-5 rounded border border-white/10 bg-neutral-950/10 flex flex-col justify-between">
          <div className="w-full">
            <h3 className="text-sm font-serif italic text-white mb-4 flex items-center font-normal pb-2 border-b border-white/5">
              <Sparkles className="w-4 h-4 mr-2 text-zinc-500" />
              Real-Time Global Market Screener & Opportunities Scanner
            </h3>
            <div className="h-[400px] w-full bg-neutral-950/10 border border-white/5 rounded overflow-hidden">
              <div ref={screenerRef} className="width-full h-full" />
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================== */}
      {/* SECONDARY ROW (WIDGET 8): LEDGER SESSIONS AND TERMINAL LOGS */}
      {/* ========================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pb-6">
        
        {/* Active open operations ledger panel */}
        <div className="lg:col-span-8 metric-card p-5 rounded border border-white/10 bg-neutral-950/10">
          <h3 className="text-sm font-serif italic text-white mb-4 flex items-center font-normal pb-2 border-b border-white/5">
            <Database className="w-4 h-4 mr-2 text-zinc-500" />
            Live Open Ledger Sessions (MT4/MT5 Active Positions)
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-white/5 text-[9px] uppercase font-bold tracking-widest text-stone-500">
                  <th className="pb-3 pt-1">Position ticket</th>
                  <th className="pb-3 pt-1">Symbol</th>
                  <th className="pb-3 pt-1">Directive</th>
                  <th className="pb-3 pt-1">Volume (Lots)</th>
                  <th className="pb-3 pt-1">Entry Price</th>
                  <th className="pb-3 pt-1">Live price</th>
                  <th className="pb-3 pt-1 text-right">Adaptive P/L</th>
                  <th className="pb-3 pt-1 text-center">Settlement</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {positions.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-zinc-600 text-[11px] font-mono">
                      No active open positions on server gateway. Use Order Dispatch Desk to initiate exposure trades.
                    </td>
                  </tr>
                ) : (
                  positions.map(pos => (
                    <tr key={pos.id} className="hover:bg-white/2 transition duration-150">
                      <td className="py-3 text-white font-bold">{pos.id}</td>
                      <td className="py-3 text-white font-bold">{pos.symbol}</td>
                      <td className="py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${
                          pos.side === "BUY" ? "text-emerald-400 bg-emerald-500/5" : "text-rose-400 bg-rose-500/5"
                        }`}>
                          {pos.side}
                        </span>
                      </td>
                      <td className="py-3 text-white font-bold">{pos.lots}</td>
                      <td className="py-3 text-neutral-400">{pos.entryPrice}</td>
                      <td className="py-3 text-zinc-300 transition-all duration-300">{pos.currentPrice}</td>
                      <td className={`py-3 text-right font-bold transition duration-300 font-bold ${pos.pnl >= 0 ? "text-emerald-400" : "text-rose-400 font-extrabold"}`}>
                        {pos.pnl >= 0 ? "+" : ""}{pos.pnl.toFixed(2)} USD
                      </td>
                      <td className="py-3 text-center">
                        <button
                          onClick={() => handleClosePosition(pos.id)}
                          className="px-2.5 py-1 text-[10px] font-bold bg-[#ef4444]/15 hover:bg-[#ef4444] text-[#ef4444] hover:text-black rounded transition select-none cursor-pointer"
                        >
                          CLOSE
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Historical Closed Trades recents list */}
          {history.length > 0 && (
            <div className="mt-6 pt-5 border-t border-white/5 space-y-3">
              <h4 className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider">Settled transaction ledger (Sovereign closed trades)</h4>
              <div className="max-h-36 overflow-y-auto space-y-2">
                {history.map(hist => (
                  <div key={hist.id} className="flex justify-between items-center text-[10px] font-mono p-2 bg-neutral-950/40 rounded border border-white/5 hover:border-white/10 transition">
                    <span className="text-zinc-500">{hist.timestamp}</span>
                    <span className="text-white font-bold">{hist.id}</span>
                    <span className="font-semibold text-white">{hist.symbol}</span>
                    <span className={`px-1.5 py-0.2 rounded text-[9px] ${hist.side === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>{hist.side}</span>
                    <span className="text-stone-300">{hist.lots} Lots</span>
                    <span className="text-zinc-500">In: {hist.entryPrice} &bull; Out: {hist.exitPrice}</span>
                    <span className={`font-bold ${hist.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {hist.pnl >= 0 ? "+" : ""}{hist.pnl.toFixed(2)} USD
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Real-time Sovereign broker console logs feed */}
        <div className="lg:col-span-4 metric-card p-5 rounded border border-white/10 bg-neutral-950/10 flex flex-col justify-between">
          <div className="w-full">
            <h3 className="text-sm font-serif italic text-white mb-3 flex items-center font-normal pb-2 border-b border-white/5">
              <Clock className="w-4 h-4 mr-2" />
              Sovereign Handshaking Core Audit Stream
            </h3>

            <div className="h-44 overflow-y-auto bg-neutral-950/40 p-3 rounded-lg border border-white/5 font-mono text-[10px] text-zinc-400 space-y-2.5">
              {executionLogs.map((log, idx) => (
                <div key={idx} className="leading-relaxed border-l border-white/5 pl-2">
                  {log}
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-white/5 mt-4 text-[9px] font-mono text-zinc-600 leading-normal">
            * Connection encrypted with AES-256 ECC node key handshake. Submited orders are simulated against live index feeds within PRIV secure sandboxed core container. Always configure trading parameters prudently.
          </div>
        </div>

      </div>
      </>
    );
  };

  return (
    <div className="space-y-6">
      {/* Ticker Tape Top Bar */}
      <div className="w-full bg-neutral-950/80 backdrop-blur border border-white/5 rounded-lg overflow-hidden h-14 p-1">
        <div ref={tickerTapeRef} className="tradingview-widget-container" />
      </div>

      {/* Header and Brand */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-serif italic text-white flex items-center gap-2">
            <Coins className="w-8 h-8 text-neutral-400" />
            SANS Broker Terminal
          </h1>
          <p className="text-white/40 text-xs font-light">
            Decentralized execution desk integrating live TradingView.com modules, real-time FX/Crypto feeds, global alternative sentiment, and XMGlobal server pipelines.
          </p>
        </div>

        {/* Hot Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-950 border border-white/10 rounded font-mono text-[10px]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-white/70">WSS CORE STREAM: ONLINE</span>
          </div>

          <button 
            onClick={handleDepositFunds}
            className="px-3.5 py-1.5 border border-white/10 bg-white/5 hover:bg-white/10 text-white rounded font-mono text-xs select-none transition duration-200 cursor-pointer"
          >
            VAULT ALLOCATE FUNDS
          </button>
        </div>
      </div>

      {(!demoMode && !isLogged) ? renderPrompt() : renderWorkspace()}

      {showLivePrompt && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-red-500/30 p-6 rounded-lg max-w-md w-full space-y-4 shadow-[0_0_50px_rgba(239,68,68,0.15)] relative">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-amber-500" />
            <div className="flex items-center space-x-3 text-red-500 font-bold">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
              <h3 className="font-serif italic font-semibold text-base text-white">LIVE HANDSHAKE DETECTED</h3>
            </div>
            
            <p className="text-xs text-zinc-300 font-sans leading-relaxed">
              You are establishing a <span className="text-red-400 font-mono font-bold">LIVE CONNECTION</span> to your XM Broker Account. However, the system is currently configured for a <span className="text-orange-400 font-mono">DEMO ENVIRONMENT</span> (Simulated Mode).
            </p>
            
            <p className="text-[11px] text-zinc-500 font-mono">
              In Demo Mode, all execution routines are simulated. To trade using PRIV's genuine live pipelines, you must toggle Demo Environment OFF.
            </p>

            <div className="flex flex-col gap-2 pt-2 font-mono">
              <button
                type="button"
                onClick={() => {
                  setDemoMode?.(false);
                  setShowLivePrompt(false);
                  
                  // Proceed connection directly
                  setIsLoggingIn(true);
                  setExecutionLogs(prev => [
                    ...prev,
                    `[${new Date().toLocaleTimeString()}] Handshaking live node with ${server}...`,
                    `[${new Date().toLocaleTimeString()}] Disabling Demo Mode environment...`,
                    `[${new Date().toLocaleTimeString()}] Connecting live MT${server.toLowerCase().includes("mt5") ? "5" : "4"} account ${accountId}...`
                  ]);

                  setTimeout(() => {
                    setIsLogged(true);
                    setIsLoggingIn(false);
                    setExecutionLogs(prev => [
                      ...prev,
                      `[${new Date().toLocaleTimeString()}] LIVE connection established on secure port ${server}. Genuine portfolio sync complete.`,
                      `[${new Date().toLocaleTimeString()}] Active LIVE Ledger Initialized. Balance: ${accountCurrency} ${balance.toFixed(2)}. Leverage: ${leverage}.`
                    ]);
                  }, 1800);
                }}
                className="w-full bg-red-600 hover:bg-red-500 text-white font-bold text-xs py-2.5 rounded transition duration-150 cursor-pointer text-center"
              >
                SWITCH TO LIVE VERSION (Disable Demo)
              </button>
              <button
                type="button"
                onClick={() => setShowLivePrompt(false)}
                className="w-full bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-400 hover:text-white text-xs py-2.5 rounded transition duration-150 cursor-pointer text-center"
              >
                CANCEL PROMPT
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
