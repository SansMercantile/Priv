import express from "express";
import fs from "fs";
import path from "path";
import {
  assetUrl,
  hasPython,
  library,
  resolveAsset,
  runAds,
  runAudit,
  runPosters,
  runStudio,
  runVideo,
  studioCatalog,
  writeSpec,
} from "./local.js";

export const marketingRouter = express.Router();

// ── engine dependency injection ──────────────────────────────────────────────
// The AI script writer reuses whatever provider server.ts already has wired
// (Bedrock or Gemini via getAIClient). server.ts calls setEngineAI() at boot
// with a generate(prompt) => Promise<string> closure; until then the script
// endpoint answers 503. This keeps a single AI credential path in the app.
type AiGenerate = (prompt: string, opts?: { model?: string }) => Promise<string>;
let aiGenerate: AiGenerate | null = null;
let aiProvider = "unset";
export function setEngineAI(gen: AiGenerate, provider: string) {
  aiGenerate = gen;
  aiProvider = provider;
}

function ok(res: express.Response, data: unknown, extra: Record<string, unknown> = {}) {
  res.json({ success: true, data, ...extra });
}

function fail(res: express.Response, err: any, status?: number) {
  const code = status || err?.status || 500;
  res.status(code >= 400 && code < 600 ? code : 500).json({
    success: false,
    error: err?.message || String(err),
    detail: err?.data ?? null,
  });
}

// ── local studio (compositor) ────────────────────────────────────────────────
marketingRouter.get("/catalog", async (_req, res) => {
  try {
    ok(res, { ...(await studioCatalog()), python: hasPython() });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.get("/library", async (req, res) => {
  try {
    const kind = typeof req.query.kind === "string" ? req.query.kind : undefined;
    ok(res, await library(kind));
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.get("/file", (req, res) => {
  const abs = resolveAsset(typeof req.query.path === "string" ? req.query.path : "");
  if (!abs) return res.status(400).json({ success: false, error: "bad path" });
  res.sendFile(abs);
});

marketingRouter.post("/posters/render", async (req, res) => {
  try {
    const spec = await writeSpec(req.body?.spec ?? req.body);
    const r = await runStudio(["studio.py", "poster", "--spec", spec]);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-500)), { status: 400 });
    ok(res, { files: r.json.files.map((f: any) => ({ ...f, url: assetUrl(f.rel) })) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/posters/slug", async (req, res) => {
  try {
    const slug = String(req.body?.slug || "").trim();
    if (!slug) throw Object.assign(new Error("slug is required"), { status: 400 });
    const formats = Array.isArray(req.body?.formats) ? req.body.formats : undefined;
    const args = ["studio.py", "poster", "--slug", slug];
    if (formats?.length) args.push("--formats", formats.join(","));
    const r = await runStudio(args);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-500)), { status: 400 });
    ok(res, { files: r.json.files.map((f: any) => ({ ...f, url: assetUrl(f.rel) })) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/posters/rerender", async (req, res) => {
  try {
    const slug = typeof req.body?.slug === "string" && req.body.slug ? req.body.slug : undefined;
    const r = await runPosters(slug);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-500)), { status: 400 });
    ok(res, { log: r.stdout.split("\n").filter(Boolean).slice(-60), seconds: Math.round(r.seconds) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/posters/audit", async (_req, res) => {
  try {
    const r = await runAudit();
    const text = `${r.stdout}\n${r.stderr}`;
    ok(res, {
      clear: text.includes("ALL CLEAR"),
      log: text.split("\n").filter(Boolean).slice(-80),
      seconds: Math.round(r.seconds),
    });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/videos/render", async (req, res) => {
  try {
    const spot = String(req.body?.spot || "").trim();
    if (!spot) throw Object.assign(new Error("spot is required"), { status: 400 });
    const r = await runVideo(spot);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-600)), { status: 400 });
    ok(res, { log: r.stdout.split("\n").filter(Boolean), seconds: Math.round(r.seconds) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/videos/custom", async (req, res) => {
  try {
    const spec = await writeSpec(req.body?.spec ?? req.body);
    const r = await runStudio(["studio.py", "video", "--spec", spec]);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-600)), { status: 400 });
    ok(res, { ...r.json, url: assetUrl(r.json.rel) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.post("/ads/render", async (req, res) => {
  try {
    const spot = String(req.body?.spot || "").trim();
    if (!spot) throw Object.assign(new Error("spot is required"), { status: 400 });
    const r = await runAds(spot);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-600)), { status: 400 });
    ok(res, { log: r.stdout.split("\n").filter(Boolean), seconds: Math.round(r.seconds) });
  } catch (err) {
    fail(res, err);
  }
});

// ── generation engine (scripts / voice / plates) ─────────────────────────────
// All in-house: script writer talks to the app's own AI provider, voice runs
// the local SAPI synthesizer, plates go to Amazon Bedrock Stable Image Ultra.
// No competitor APIs anywhere in this stack.

marketingRouter.get("/engine/status", (_req, res) => {
  ok(res, {
    python: hasPython(),
    ai: { provider: aiProvider, ready: Boolean(aiGenerate) },
    tts: { engine: "local SAPI (System.Speech)", rate: -1 },
    plates: { provider: "Amazon Bedrock", model: "stability.stable-image-ultra-v1:1", region: "us-west-2" },
  });
});

// Script writer: marketing copy generated by the app's own AI provider.
const SCRIPT_KINDS: Record<string, string> = {
  hook: "One scroll-stopping hook line for paid social (under 12 words).",
  caption: "One social caption (1-2 sentences) with a light CTA.",
  headline: "Three poster headline options (each under 8 words).",
  script: "A full video script: hook, problem, product as the fix, proof, CTA. Short punchy sentences.",
  email: "A short marketing email: subject line, 2-sentence body, CTA.",
};

marketingRouter.post("/engine/script", async (req, res) => {
  try {
    if (!aiGenerate) {
      throw Object.assign(new Error("AI provider not wired yet — server boot incomplete"), { status: 503 });
    }
    const kind = String(req.body?.kind || "script");
    const topic = String(req.body?.topic || "").trim();
    const detail = String(req.body?.detail || "").trim();
    const angle = String(req.body?.angle || "").trim();
    if (!SCRIPT_KINDS[kind]) {
      throw Object.assign(new Error(`kind must be one of: ${Object.keys(SCRIPT_KINDS).join(", ")}`), { status: 400 });
    }
    if (!topic) throw Object.assign(new Error("topic is required"), { status: 400 });
    const prompt = [
      "You are the in-house copywriter for Priv, an AI trading terminal by Sans Mercantile.",
      "Voice: confident, concrete, no hype. Short sentences. Trading-native.",
      "House proof points: one market, seven timeframes; every ticket ships entry, two targets and a stop; a 28-second decision cycle, audited every run; your money never leaves your own broker; start free, no card required.",
      `Task: ${SCRIPT_KINDS[kind]}`,
      `Topic: ${topic}`,
      detail ? `Extra context: ${detail}` : "",
      angle ? `Tone angle: ${angle}` : "",
      "Return only the copy, no preamble, no quotes around it.",
    ].filter(Boolean).join("\n");
    const text = (await aiGenerate(prompt)).trim();
    ok(res, { kind, topic, text });
  } catch (err) {
    fail(res, err);
  }
});

// Voice Lab: local SAPI synthesis; optionally install the clip as a scene
// take so the compositor uses it on the next render of that spot.
marketingRouter.post("/engine/tts", async (req, res) => {
  try {
    const spec = req.body?.spec ?? req.body;
    if (!spec?.text) throw Object.assign(new Error("text is required"), { status: 400 });
    const r = await runStudio(["studio.py", "tts", "--spec", await writeSpec(spec)], 120000);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-500)), { status: 400 });
    const d = r.json;
    ok(res, {
      seconds: d.seconds,
      voice: d.voice,
      rate: d.rate,
      wav: d.wav && { ...d.wav, url: assetUrl(d.wav.rel) },
      m4a: d.m4a && { ...d.m4a, url: assetUrl(d.m4a.rel) },
      installed: d.installed && { ...d.installed, url: assetUrl(d.installed.rel) },
    });
  } catch (err) {
    fail(res, err);
  }
});

// Plate Foundry: one ad-hoc background via Amazon Bedrock Stable Image Ultra.
marketingRouter.post("/engine/plate", async (req, res) => {
  try {
    const spec = req.body?.spec ?? req.body;
    if (!spec?.prompt) throw Object.assign(new Error("prompt is required"), { status: 400 });
    const r = await runStudio(["studio.py", "plate", "--spec", await writeSpec(spec)], 180000);
    if (!r.ok) throw Object.assign(new Error((r.stderr || r.stdout).slice(-500)), { status: 400 });
    ok(res, { ...r.json, url: assetUrl(r.json.rel) });
  } catch (err) {
    fail(res, err);
  }
});

marketingRouter.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "marketing-studio",
    engine: "in-house",
    python: hasPython(),
    assets: fs.existsSync(path.join(process.cwd(), "marketing", "assets")),
  });
});
