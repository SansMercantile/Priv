import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Clapperboard,
  Copy,
  ExternalLink,
  FolderOpen,
  Loader2,
  Palette,
  Play,
  RefreshCw,
  Settings,
  ShieldCheck,
  Sparkles,
  Mic,
  Image as ImageIcon,
  PenLine,
} from "lucide-react";
import { userHeader } from "../lib/userHeader";

// ── Marketing Studio ─────────────────────────────────────────────────────────
// One dashboard surface for every campaign asset — 100% in-house. Posters and
// videos render on this machine via marketing/build/studio.py (Pillow +
// ffmpeg). Generation runs through our own stack: scripts via the app's AI
// provider (Bedrock/Gemini), voice via the local SAPI synthesizer, plates via
// Amazon Bedrock Stable Image Ultra. No competitor APIs anywhere.

type Tab = "library" | "posters" | "videos" | "engine";

type Catalog = {
  formats: Record<string, [number, number]>;
  plates: string[];
  body_kinds: Record<string, { label: string; fields: Record<string, any> }>;
  posters: Array<{
    slug: string;
    plate: string;
    eyebrow: string;
    headline: string;
    sub: string;
    body: any;
    cta: string;
    formats: string[];
  }>;
  video_spots: Array<{
    name: string;
    kind?: string;
    size: [number, number];
    target?: number | null;
    out: string;
    scenes: number;
    voiced: number;
    reuse?: string | null;
  }>;
  voices?: Array<{ id: string; label: string }>;
  plate_ratios?: string[];
  plate_styles?: string[];
  paths: Record<string, string>;
  python?: string;
};

type LibraryEntry = { name: string; rel: string; url: string; size: number; kind: string };

async function ms(path: string, init?: RequestInit & { json?: unknown }) {
  const headers: Record<string, string> = { ...(await userHeader()) };
  let body: BodyInit | undefined;
  if (init?.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.json);
  }
  const res = await fetch(path, {
    method: init?.method || (init?.json !== undefined ? "POST" : "GET"),
    headers,
    body,
  });
  const text = await res.text();
  let data: any;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`Non-JSON response (HTTP ${res.status}): ${text.slice(0, 140)}`);
  }
  if (!res.ok || data?.success === false) {
    throw Object.assign(new Error(data?.error || data?.detail || `HTTP ${res.status}`), {
      detail: data?.detail ?? null,
      status: res.status,
    });
  }
  return data?.data ?? data;
}

function fmtBytes(n: number) {
  if (n > 1e6) return `${(n / 1e6).toFixed(1)} MB`;
  if (n > 1e3) return `${(n / 1e3).toFixed(0)} KB`;
  return `${n} B`;
}

const btn =
  "px-3 py-1.5 rounded-lg border font-mono text-xs font-bold transition disabled:opacity-50 cursor-pointer";
const btnPrimary = `${btn} bg-rose-950/30 text-rose-300 border-rose-500/40 hover:bg-rose-900/40`;
const btnGhost = `${btn} bg-zinc-950/50 text-zinc-300 border-zinc-800 hover:text-white hover:bg-zinc-900/70`;
const inputCls =
  "w-full bg-zinc-950/70 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-rose-500/50";
const labelCls = "block text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-wider mb-1";

function JsonView({ data, max = 240 }: { data: unknown; max?: number }) {
  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  if (!text) return null;
  return (
    <pre className="bg-black/40 border border-zinc-900 rounded-lg p-3 text-[11px] font-mono text-zinc-300 overflow-auto whitespace-pre-wrap break-all" style={{ maxHeight: max }}>
      {text.length > 20000 ? `${text.slice(0, 20000)}\n… (${text.length - 20000} more chars)` : text}
    </pre>
  );
}

function ErrorBar({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-300 text-sm rounded-lg p-3">
      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
      <span className="flex-1 break-all">{error}</span>
    </div>
  );
}

// ── Library ──────────────────────────────────────────────────────────────────
function LibraryTab() {
  const [folder, setFolder] = useState("posters");
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const folders = ["posters", "posters/custom", "videos", "storyboards", "backgrounds", "brand"];

  const load = useCallback(async (kind?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await ms(`/api/marketing/library${kind ? `?kind=${encodeURIComponent(kind)}` : ""}`);
      setEntries(data[kind || folder] || []);
    } catch (e: any) {
      setError(e.message);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [folder]);

  useEffect(() => {
    load(folder);
  }, [folder, load]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {folders.map((f) => (
          <button key={f} onClick={() => setFolder(f)} className={`${folder === f ? btnPrimary : btnGhost} cursor-pointer`}>
            {f}
          </button>
        ))}
        <button onClick={() => load(folder)} className={`${btnGhost} ml-auto cursor-pointer`}>
          <RefreshCw className="w-3 h-3 inline mr-1" />
          Refresh
        </button>
      </div>
      <ErrorBar error={error} />
      {loading ? (
        <div className="flex items-center gap-2 text-white/60 p-6">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading assets…
        </div>
      ) : entries.length === 0 ? (
        <div className="text-zinc-500 text-sm p-6 border border-dashed border-zinc-800 rounded-lg">No assets in this folder yet.</div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          {entries.map((e) => (
            <div key={e.rel} className="bg-white/5 border border-white/10 rounded-xl overflow-hidden group">
              <a href={e.url} target="_blank" rel="noreferrer" className="block aspect-square bg-black/60">
                {e.kind === "video" ? (
                  <video src={e.url} muted className="w-full h-full object-cover" />
                ) : (
                  <img src={e.url} alt={e.name} loading="lazy" className="w-full h-full object-contain" />
                )}
              </a>
              <div className="p-2 space-y-1">
                <div className="text-[10px] font-mono text-zinc-400 truncate" title={e.rel}>{e.name}</div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-zinc-600">{fmtBytes(e.size)}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`${window.location.origin}${e.url}`);
                      setCopied(e.rel);
                      setTimeout(() => setCopied(null), 1200);
                    }}
                    className="text-zinc-500 hover:text-rose-300 cursor-pointer"
                    title="Copy URL"
                  >
                    {copied === e.rel ? <ShieldCheck className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Poster Studio ────────────────────────────────────────────────────────────
function PostersTab({ catalog }: { catalog: Catalog | null }) {
  const [template, setTemplate] = useState("");
  const [headline, setHeadline] = useState("");
  const [eyebrow, setEyebrow] = useState("");
  const [sub, setSub] = useState("");
  const [cta, setCta] = useState("");
  const [plate, setPlate] = useState("");
  const [bodyJson, setBodyJson] = useState("");
  const [formats, setFormats] = useState<string[]>(["feed"]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any[]>([]);
  const [auditLog, setAuditLog] = useState<string[]>([]);

  const posters = catalog?.posters || [];
  const plates = catalog?.plates || [];
  const allFormats = Object.keys(catalog?.formats || { feed: [1, 1], story: [1, 1], wide: [1, 1], thumb: [1, 1], link: [1, 1] });

  useEffect(() => {
    if (!template || !catalog) return;
    const p = catalog.posters.find((x) => x.slug === template);
    if (!p) return;
    setHeadline(p.headline);
    setEyebrow(p.eyebrow);
    setSub(p.sub);
    setCta(p.cta);
    setPlate(p.plate);
    setFormats(p.formats);
    setBodyJson(p.body ? JSON.stringify(p.body, null, 2) : "");
  }, [template, catalog]);

  const render = async () => {
    setBusy("render");
    setError(null);
    setResult([]);
    try {
      const spec: any = { slug: template || "custom", headline, plate, formats };
      if (eyebrow) spec.eyebrow = eyebrow;
      if (sub) spec.sub = sub;
      if (cta) spec.cta = cta;
      if (template) spec.template = template;
      if (bodyJson.trim()) spec.body = JSON.parse(bodyJson);
      const data = await ms("/api/marketing/posters/render", { json: { spec } });
      setResult(data.files || []);
    } catch (e: any) {
      setError(e.message.includes("Unexpected token") || e.message.includes("JSON") ? `${e.message} — check the body JSON` : e.message);
    } finally {
      setBusy(null);
    }
  };

  const rerenderAll = async () => {
    setBusy("rerender");
    setError(null);
    setAuditLog([]);
    try {
      const data = await ms("/api/marketing/posters/rerender", { json: {} });
      setAuditLog(data.log || []);
      setResult([]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const audit = async () => {
    setBusy("audit");
    setError(null);
    try {
      const data = await ms("/api/marketing/posters/audit", { json: {} });
      setAuditLog([data.clear ? "✓ ALL CLEAR" : "✗ AUDIT FAILED", ...(data.log || [])]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <ErrorBar error={error} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
          <div className="text-xs font-mono font-bold text-rose-300">RENDER POSTER</div>
          <div>
            <label className={labelCls}>Template (clone an existing design)</label>
            <select value={template} onChange={(e) => setTemplate(e.target.value)} className={inputCls}>
              <option value="">— custom —</option>
              {posters.map((p) => (
                <option key={p.slug} value={p.slug}>{p.slug}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Headline *</label>
              <input value={headline} onChange={(e) => setHeadline(e.target.value)} className={inputCls} placeholder="Execution, automated." />
            </div>
            <div>
              <label className={labelCls}>Eyebrow</label>
              <input value={eyebrow} onChange={(e) => setEyebrow(e.target.value)} className={inputCls} placeholder="SANS NETWORK" />
            </div>
          </div>
          <div>
            <label className={labelCls}>Subline</label>
            <input value={sub} onChange={(e) => setSub(e.target.value)} className={inputCls} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Plate *</label>
              <select value={plate} onChange={(e) => setPlate(e.target.value)} className={inputCls}>
                <option value="">— pick —</option>
                {plates.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>CTA</label>
              <input value={cta} onChange={(e) => setCta(e.target.value)} className={inputCls} placeholder="Start free →" />
            </div>
          </div>
          <div>
            <label className={labelCls}>Body (JSON — kind: signal|chips|bullets|stats|tiers|platforms|agents|notify)</label>
            <textarea value={bodyJson} onChange={(e) => setBodyJson(e.target.value)} rows={4} className={`${inputCls} font-mono text-xs`} placeholder='{"kind":"bullets","items":["Live SANS signals","14-day free trial"]}' />
          </div>
          <div>
            <label className={labelCls}>Formats</label>
            <div className="flex flex-wrap gap-2">
              {allFormats.map((f) => (
                <label key={f} className="flex items-center gap-1 text-xs text-zinc-300 bg-zinc-950/60 border border-zinc-800 rounded-lg px-2 py-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formats.includes(f)}
                    onChange={(ev) => setFormats(ev.target.checked ? [...formats, f] : formats.filter((x) => x !== f))}
                  />
                  {f}
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2 pt-1">
            <button onClick={render} disabled={busy !== null || !headline || !plate} className={btnPrimary}>
              {busy === "render" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <Palette className="w-3 h-3 inline mr-1" />}
              Render
            </button>
            <button onClick={rerenderAll} disabled={busy !== null} className={btnGhost}>
              {busy === "rerender" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <RefreshCw className="w-3 h-3 inline mr-1" />}
              Re-render all 38
            </button>
            <button onClick={audit} disabled={busy !== null} className={btnGhost}>
              {busy === "audit" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <ShieldCheck className="w-3 h-3 inline mr-1" />}
              Audit
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {result.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
              <div className="text-xs font-mono font-bold text-emerald-300">RENDERED ({result.length})</div>
              <div className="grid grid-cols-2 gap-3">
                {result.map((f: any) => (
                  <div key={f.rel} className="space-y-1">
                    <a href={f.url} target="_blank" rel="noreferrer" className="block bg-black/50 rounded-lg overflow-hidden">
                      <img src={f.url} alt={f.file} className="w-full object-contain" />
                    </a>
                    <div className="text-[10px] font-mono text-zinc-500">
                      {f.format} · {f.width}×{f.height}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {auditLog.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="text-xs font-mono font-bold text-zinc-400 mb-2">LOG</div>
              <JsonView data={auditLog.join("\n")} max={360} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Video Studio ─────────────────────────────────────────────────────────────
function VideosTab({ catalog }: { catalog: Catalog | null }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [customSpec, setCustomSpec] = useState(
    `{
  "name": "custom-spot",
  "size": [1080, 1920],
  "target": 15,
  "scenes": [
    { "plate": "grid-dark", "eyebrow": "SANS NETWORK", "headline": "Scene one", "sub": "First beat" },
    { "plate": "grid-dark", "headline": "Scene two", "vo": "A voice-over line", "hold": 4 }
  ]
}`
  );

  const spots = catalog?.video_spots || [];
  const plates = catalog?.plates || [];

  const renderSpot = async (spot: { name: string; kind?: string; out: string }) => {
    const isAd = spot.kind === "ad" || spot.name.startsWith("ad-");
    setBusy(spot.name);
    setError(null);
    setLog([]);
    setVideoUrl(null);
    try {
      const data = await ms(isAd ? "/api/marketing/ads/render" : "/api/marketing/videos/render", { json: { spot: spot.name } });
      setLog(data.log || []);
      setVideoUrl(`/marketing-assets/videos/${spot.out}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const renderCustom = async () => {
    setBusy("custom");
    setError(null);
    setLog([]);
    setVideoUrl(null);
    try {
      const spec = JSON.parse(customSpec);
      const data = await ms("/api/marketing/videos/custom", { json: { spec } });
      setLog(data.log || []);
      setVideoUrl(data.url);
    } catch (e: any) {
      setError(e.message.includes("Unexpected token") ? "Custom spec is not valid JSON" : e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <ErrorBar error={error} />
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <div className="px-4 py-2 border-b border-white/10 text-xs font-mono font-bold text-rose-300">CAMPAIGN SPOTS</div>
        <div className="divide-y divide-white/5">
          {spots.map((s) => (
            <div key={s.name} className="flex items-center gap-3 px-4 py-2.5 flex-wrap">
              <div className="flex-1 min-w-[180px]">
                <div className="text-sm text-white font-medium">{s.name}</div>
                <div className="text-[10px] font-mono text-zinc-500">
                  {s.kind === "ad" ? "AD" : "CAMPAIGN"} · {s.size[0]}×{s.size[1]} · {s.scenes} scenes{s.voiced ? ` · ${s.voiced} voiced` : ""}
                  {s.target ? ` · target ${s.target}s` : ""}
                </div>
              </div>
              <button onClick={() => renderSpot(s)} disabled={busy !== null} className={btnGhost}>
                {busy === s.name ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <Play className="w-3 h-3 inline mr-1" />}
                Render
              </button>
            </div>
          ))}
        </div>
      </div>

      {videoUrl && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-2">
          <div className="text-xs font-mono font-bold text-emerald-300">OUTPUT</div>
          <video src={videoUrl} controls className="w-full max-h-96 rounded-lg bg-black" />
          <a href={videoUrl} target="_blank" rel="noreferrer" className="text-xs font-mono text-rose-300 hover:underline inline-flex items-center gap-1">
            <ExternalLink className="w-3 h-3" /> {videoUrl}
          </a>
        </div>
      )}

      <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
        <div className="text-xs font-mono font-bold text-zinc-400">CUSTOM VIDEO (JSON spec — plates: {plates.slice(0, 6).join(", ")}…)</div>
        <textarea value={customSpec} onChange={(e) => setCustomSpec(e.target.value)} rows={12} className={`${inputCls} font-mono text-xs`} spellCheck={false} />
        <button onClick={renderCustom} disabled={busy !== null} className={btnPrimary}>
          {busy === "custom" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <Clapperboard className="w-3 h-3 inline mr-1" />}
          Render custom video
        </button>
      </div>

      {log.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <div className="text-xs font-mono font-bold text-zinc-400 mb-2">RENDER LOG</div>
          <JsonView data={log.join("\n")} max={320} />
        </div>
      )}
    </div>
  );
}

// ── Generation Engine ────────────────────────────────────────────────────────
function EngineTab({ catalog }: { catalog: Catalog | null }) {
  const [status, setStatus] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Script Writer
  const [kind, setKind] = useState("script");
  const [topic, setTopic] = useState("");
  const [detail, setDetail] = useState("");
  const [script, setScript] = useState("");

  // Voice Lab
  const [voiceText, setVoiceText] = useState("");
  const [voice, setVoice] = useState(catalog?.voices?.[0]?.id || "Microsoft David Desktop");
  const [installSpot, setInstallSpot] = useState("");
  const [installScene, setInstallScene] = useState("1");
  const [voiceOut, setVoiceOut] = useState<any>(null);

  // Plate Foundry
  const [platePrompt, setPlatePrompt] = useState("");
  const [plateRatio, setPlateRatio] = useState("9:16");
  const [plateStyle, setPlateStyle] = useState("campaign");
  const [plateOut, setPlateOut] = useState<any>(null);

  const spots = catalog?.video_spots || [];
  const voices = catalog?.voices || [];

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await ms("/api/marketing/engine/status");
        if (!cancelled) setStatus(d);
      } catch {
        /* status is best-effort */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const genScript = async () => {
    setBusy("script");
    setError(null);
    try {
      const d = await ms("/api/marketing/engine/script", { json: { kind, topic, detail } });
      setScript(d.text);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const genVoice = async () => {
    setBusy("voice");
    setError(null);
    setVoiceOut(null);
    try {
      const spec: any = { text: voiceText, voice };
      if (installSpot.trim()) {
        spec.install = { spot: installSpot.trim(), scene: Number(installScene) || 1 };
      }
      setVoiceOut(await ms("/api/marketing/engine/tts", { json: { spec } }));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  const genPlate = async () => {
    setBusy("plate");
    setError(null);
    setPlateOut(null);
    try {
      setPlateOut(await ms("/api/marketing/engine/plate", { json: { prompt: platePrompt, ratio: plateRatio, style: plateStyle } }));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-4">
      <ErrorBar error={error} />

      <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-mono">
        <span className="text-zinc-500">
          AI: <span className={status?.ai?.ready ? "text-emerald-300" : "text-amber-300"}>{status?.ai?.provider || "…"}</span>
        </span>
        <span className="text-zinc-500">
          TTS: <span className="text-zinc-300">{status?.tts?.engine || "…"}</span>
        </span>
        <span className="text-zinc-500">
          Plates: <span className="text-zinc-300">{status?.plates?.provider || "…"}</span>
        </span>
        <span className="text-zinc-500">
          Renderer: <span className={status?.python ? "text-emerald-300" : "text-amber-300"}>{status?.python ? "local Pillow+ffmpeg" : "python missing"}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Script Writer */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-300">
            <PenLine className="w-3.5 h-3.5" /> SCRIPT WRITER
          </div>
          <div className="flex gap-2">
            <select value={kind} onChange={(e) => setKind(e.target.value)} className={inputCls}>
              <option value="script">video script</option>
              <option value="hook">hook line</option>
              <option value="caption">social caption</option>
              <option value="headline">poster headlines</option>
              <option value="email">email</option>
            </select>
          </div>
          <input value={topic} onChange={(e) => setTopic(e.target.value)} className={inputCls} placeholder="Topic — e.g. why every ticket ships a stop" />
          <textarea value={detail} onChange={(e) => setDetail(e.target.value)} rows={2} className={inputCls} placeholder="Extra context (optional)" />
          <button onClick={genScript} disabled={busy !== null || !topic.trim()} className={btnPrimary}>
            {busy === "script" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <Sparkles className="w-3 h-3 inline mr-1" />}
            Write
          </button>
          {script && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="text-[10px] font-mono font-bold text-emerald-300">DRAFT</div>
                <button onClick={() => navigator.clipboard.writeText(script)} className="text-zinc-500 hover:text-rose-300 cursor-pointer" title="Copy">
                  <Copy className="w-3 h-3" />
                </button>
              </div>
              <textarea readOnly value={script} rows={8} className={`${inputCls} font-mono text-xs`} />
            </div>
          )}
        </div>

        {/* Voice Lab */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-300">
            <Mic className="w-3.5 h-3.5" /> VOICE LAB
          </div>
          <textarea value={voiceText} onChange={(e) => setVoiceText(e.target.value)} rows={3} className={inputCls} placeholder="Line to synthesize — e.g. Entry. Two targets. One stop." />
          <div className="grid grid-cols-2 gap-2">
            <select value={voice} onChange={(e) => setVoice(e.target.value)} className={inputCls}>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>{v.label}</option>
              ))}
              {!voices.length && <option value="Microsoft David Desktop">David — male, house default</option>}
            </select>
            <input value={installSpot} onChange={(e) => setInstallSpot(e.target.value)} className={inputCls} placeholder="install into spot (optional)" list="studio-spots" />
            <datalist id="studio-spots">
              {spots.map((s) => (
                <option key={s.name} value={s.name} />
              ))}
            </datalist>
            <input value={installScene} onChange={(e) => setInstallScene(e.target.value)} className={inputCls} placeholder="scene # (1)" />
          </div>
          <button onClick={genVoice} disabled={busy !== null || !voiceText.trim()} className={btnPrimary}>
            {busy === "voice" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <Mic className="w-3 h-3 inline mr-1" />}
            Synthesize
          </button>
          {voiceOut && (
            <div className="space-y-2">
              <div className="text-[10px] font-mono text-zinc-500">
                {voiceOut.seconds}s · {voiceOut.voice}
                {voiceOut.installed ? ` · installed as ${voiceOut.installed.spot}/scene-${String(voiceOut.installed.scene).padStart(2, "0")} (takes win on next render)` : " · draft only"}
              </div>
              <audio src={voiceOut.m4a?.url} controls className="w-full" />
            </div>
          )}
        </div>

        {/* Plate Foundry */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3 lg:col-span-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-300">
            <ImageIcon className="w-3.5 h-3.5" /> PLATE FOUNDRY
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input value={platePrompt} onChange={(e) => setPlatePrompt(e.target.value)} className={`${inputCls} sm:col-span-2`} placeholder="Describe the plate — e.g. a circular brushed-metal vault door with gold rings, dark navy room" />
            <div className="flex gap-2">
              <select value={plateRatio} onChange={(e) => setPlateRatio(e.target.value)} className={inputCls}>
                {(catalog?.plate_ratios || ["16:9", "9:16", "4:5", "1:1"]).map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
              <select value={plateStyle} onChange={(e) => setPlateStyle(e.target.value)} className={inputCls}>
                {(catalog?.plate_styles || ["campaign", "ads"]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          <button onClick={genPlate} disabled={busy !== null || !platePrompt.trim()} className={btnPrimary}>
            {busy === "plate" ? <Loader2 className="w-3 h-3 inline animate-spin mr-1" /> : <ImageIcon className="w-3 h-3 inline mr-1" />}
            Generate plate
          </button>
          {plateOut && (
            <div className="flex flex-wrap items-start gap-4">
              <a href={plateOut.url} target="_blank" rel="noreferrer" className="block bg-black/50 rounded-lg overflow-hidden w-48">
                <img src={plateOut.url} alt={plateOut.name} className="w-full object-contain" />
              </a>
              <div className="text-xs font-mono text-zinc-400 space-y-1">
                <div className="text-emerald-300 font-bold">{plateOut.provider === "bedrock" ? "✓ Bedrock Stable Image Ultra" : "⚠ procedural fallback (no Bedrock creds)"}</div>
                <div>{plateOut.name} · {plateOut.ratio} · {plateOut.seconds}s</div>
                <div className="text-zinc-500">{plateOut.rel}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Shell ────────────────────────────────────────────────────────────────────
export default function MarketingStudio() {
  const [tab, setTab] = useState<Tab>("library");
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await ms("/api/marketing/catalog");
        if (!cancelled) setCatalog(data);
      } catch (e: any) {
        if (!cancelled) setCatalogError(e.message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const tabs: Array<{ id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: "library", label: "Library", icon: FolderOpen },
    { id: "posters", label: "Poster Studio", icon: Palette },
    { id: "videos", label: "Video Studio", icon: Clapperboard },
    { id: "engine", label: "Engine", icon: Settings },
  ];

  return (
    <div className="p-2 sm:p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-rose-400" />
        <h1 className="text-xl font-semibold text-white">Marketing Studio</h1>
        <span className="text-[10px] font-mono text-zinc-500 border border-zinc-800 rounded px-1.5 py-0.5">
          in-house engine
        </span>
        <span className="text-[10px] font-mono text-zinc-500 border border-zinc-800 rounded px-1.5 py-0.5">
          {catalog ? `${catalog.posters.length} posters · ${catalog.video_spots.length} spots · ${catalog.plates.length} plates` : "loading…"}
        </span>
      </div>

      {catalogError && (
        <div className="text-xs font-mono text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2">
          Catalog unavailable: {catalogError} — poster/video tabs need the local renderer running.
        </div>
      )}

      <div className="flex border-b border-zinc-900 pb-3 gap-2 overflow-x-auto scrollbar-hide">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg font-mono text-xs font-bold transition duration-150 whitespace-nowrap cursor-pointer ${
                tab === t.id
                  ? "bg-rose-950/20 text-rose-400 border-rose-500/30 shadow-[0_0_8px_rgba(225,29,72,0.1)]"
                  : "bg-zinc-950/50 text-zinc-400 border-zinc-900 hover:text-white hover:bg-zinc-900/60"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === "library" && <LibraryTab />}
      {tab === "posters" && <PostersTab catalog={catalog} />}
      {tab === "videos" && <VideosTab catalog={catalog} />}
      {tab === "engine" && <EngineTab catalog={catalog} />}
    </div>
  );
}
