/**
 * ═══════════════════════════════════════════════════════
 *  PRIV — Anti-Bot & Anti-Scraper Middleware
 *  Blocks crawlers, scrapers, AI harvesters, and headless
 *  browsers before they reach any application logic.
 * ═══════════════════════════════════════════════════════
 */

import { Request, Response, NextFunction } from "express";

// ── 1. Known bad User-Agent substrings ───────────────────────────────────────
const BOT_UA_PATTERNS: RegExp[] = [
  // Generic crawlers / spiders
  /bot/i, /spider/i, /crawl/i, /slurp/i, /scraper/i, /fetcher/i,
  /archiver/i, /wget/i, /curl/i, /python-requests/i, /go-http-client/i,
  /java\//i, /okhttp/i, /axios/i, /libwww/i, /httpclient/i,
  /mechanize/i, /scrapy/i, /phantomjs/i, /selenium/i, /playwright/i,
  /puppeteer/i, /headless/i, /htmlunit/i, /jsdom/i,
  // Specific named bots
  /googlebot/i, /bingbot/i, /yandex/i, /baiduspider/i, /duckduckbot/i,
  /facebot/i, /ia_archiver/i, /wayback/i, /archive\.org/i,
  /semrushbot/i, /ahrefsbot/i, /mj12bot/i, /dotbot/i, /petalbot/i,
  /dataforseobot/i, /applebot/i, /twitterbot/i, /linkedinbot/i,
  // AI / LLM training harvesters
  /gptbot/i, /chatgpt/i, /ccbot/i, /anthropic/i, /claude/i,
  /cohere/i, /perplexity/i, /amazonbot/i, /diffbot/i, /bytespider/i,
  /google-extended/i, /meta-externalagent/i, /omgili/i, /dataprovider/i,
];

// ── 2. Headless browser fingerprint check ────────────────────────────────────
function hasHeadlessBrowserFingerprint(req: Request): boolean {
  const ua = req.headers["user-agent"] || "";
  if (!req.headers["accept-language"]) return true;
  if (!req.headers["accept"]) return true;
  const secFetchSite = req.headers["sec-fetch-site"];
  const secFetchMode = req.headers["sec-fetch-mode"];
  if (
    req.method === "GET" &&
    !req.path.startsWith("/api/") &&
    !secFetchSite &&
    !secFetchMode
  ) {
    if (!ua.includes("Mozilla")) return true;
  }
  return false;
}

// ── 3. Rate-limit store (in-process; swap for Redis in production) ────────────
const requestCounts = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT_WINDOW_MS = 60_000;  // 1 minute window
const RATE_LIMIT_MAX_REQUESTS = 120;  // max requests per IP per window

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const entry = requestCounts.get(ip);
  if (!entry || now > entry.resetAt) {
    requestCounts.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return false;
  }
  entry.count++;
  return entry.count > RATE_LIMIT_MAX_REQUESTS;
}

// ── 4. IP blocklist ───────────────────────────────────────────────────────────
const BLOCKED_IPS = new Set<string>([
  // Add known scraper IPs here e.g.: "1.2.3.4",
]);

// ── 5. Main anti-bot middleware ───────────────────────────────────────────────
export function antiBotMiddleware(req: Request, res: Response, next: NextFunction): void {
  // Always allow health checks and API routes without bot filtering
  if (req.path === "/api/health" || req.path.startsWith("/api/")) {
    return next();
  }

  const ip = (
    req.headers["x-forwarded-for"]?.toString().split(",")[0].trim() ||
    req.socket.remoteAddress ||
    "unknown"
  );

  if (BLOCKED_IPS.has(ip)) {
    res.status(403).set("X-Blocked-Reason", "ip-blocklist").end();
    return;
  }
  if (isRateLimited(ip)) {
    res.status(429).set("Retry-After", "60").set("X-Blocked-Reason", "rate-limit")
      .json({ error: "Too many requests." });
    return;
  }
  const ua = req.headers["user-agent"] || "";
  if (!ua || BOT_UA_PATTERNS.some((pattern) => pattern.test(ua))) {
    res.status(403).set("X-Blocked-Reason", "bot-ua").end();
    return;
  }
  if (hasHeadlessBrowserFingerprint(req)) {
    res.status(403).set("X-Blocked-Reason", "headless-fingerprint").end();
    return;
  }
  next();
}

// ── 6. Security headers middleware ────────────────────────────────────────────
export function securityHeadersMiddleware(_req: Request, res: Response, next: NextFunction): void {
  res.set("X-Frame-Options", "DENY");
  res.set("X-Content-Type-Options", "nosniff");
  res.set("Referrer-Policy", "no-referrer");
  res.set("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload");
  res.set("X-Robots-Tag", "noindex, nofollow, noarchive, nosnippet, noimageindex");
  res.set("Cache-Control", "no-store, no-cache, must-revalidate, private");
  res.set("Pragma", "no-cache");
  res.set(
    "Content-Security-Policy",
    [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "connect-src 'self' https://api.anthropic.com https://generativelanguage.googleapis.com https://query1.finance.yahoo.com https://mcp.us5.datadoghq.com",
      "frame-ancestors 'none'",
      "form-action 'self'",
    ].join("; ")
  );
  res.set(
    "Permissions-Policy",
    "geolocation=(), camera=(), microphone=(), payment=(), usb=(), interest-cohort=()"
  );
  next();
}
