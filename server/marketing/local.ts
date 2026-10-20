import { spawn } from "child_process";
import fs from "fs";
import path from "path";

const REPO = process.cwd();
export const MARKETING_DIR = path.join(REPO, "marketing");
export const ASSETS_DIR = path.join(MARKETING_DIR, "assets");
const BUILD_DIR = path.join(MARKETING_DIR, "build");
const PY =
  process.env.PRIV_PYTHON ||
  "C:\\Users\\kpasc\\.bridge\\venv\\Scripts\\python.exe";
const STUDIO_TIMEOUT_MS = Number(process.env.STUDIO_TIMEOUT_MS || 900000);

const IMAGE_EXT = new Set([".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif", ".ico"]);
const VIDEO_EXT = new Set([".mp4", ".webm", ".mov", ".m4v"]);

export type StudioResult = {
  ok: boolean;
  code: number | null;
  json: any;
  stdout: string;
  stderr: string;
  seconds: number;
};

export function runStudio(args: string[], timeoutMs = STUDIO_TIMEOUT_MS): Promise<StudioResult> {
  return new Promise((resolve) => {
    const started = Date.now();
    const child = spawn(PY, args, { cwd: BUILD_DIR, windowsHide: true });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));
    const timer = setTimeout(() => {
      child.kill();
      resolve({ ok: false, code: null, json: null, stdout, stderr: stderr + "\ntimeout", seconds: (Date.now() - started) / 1000 });
    }, timeoutMs);
    child.on("close", (code) => {
      clearTimeout(timer);
      let json: any = null;
      try {
        json = JSON.parse(stdout);
      } catch {
        json = null;
      }
      resolve({ ok: code === 0 && json !== null, code, json, stdout, stderr, seconds: (Date.now() - started) / 1000 });
    });
    child.on("error", (err) => {
      clearTimeout(timer);
      resolve({ ok: false, code: null, json: null, stdout, stderr: String(err), seconds: (Date.now() - started) / 1000 });
    });
  });
}

export async function studioCatalog() {
  const r = await runStudio(["studio.py", "catalog"], 120000);
  if (!r.ok) throw new Error(`studio catalog failed: ${(r.stderr || r.stdout).slice(-400)}`);
  return r.json;
}

export async function writeSpec(payload: unknown): Promise<string> {
  const dir = path.join(BUILD_DIR, ".studio");
  await fs.promises.mkdir(dir, { recursive: true });
  const file = path.join(dir, `spec-${Date.now()}-${Math.random().toString(36).slice(2, 8)}.json`);
  await fs.promises.writeFile(file, JSON.stringify(payload), "utf-8");
  return file;
}

export function resolveAsset(rel: string): string | null {
  if (typeof rel !== "string" || !rel.trim()) return null;
  const clean = rel.replace(/\\/g, "/").replace(/^\/+/, "");
  if (clean.includes("..")) return null;
  const abs = path.resolve(ASSETS_DIR, clean);
  if (!abs.startsWith(ASSETS_DIR + path.sep)) return null;
  return fs.existsSync(abs) ? abs : null;
}

export function assetUrl(rel: string): string {
  return "/marketing-assets/" + rel.replace(/\\/g, "/").replace(/^\/+/, "");
}

type Entry = { name: string; rel: string; url: string; size: number; kind: string };

async function walk(dir: string, base: string, out: Entry[], limit: number) {
  if (out.length >= limit) return;
  let items: fs.Dirent[];
  try {
    items = await fs.promises.readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const item of items) {
    if (out.length >= limit) return;
    if (item.name.startsWith(".")) continue;
    const abs = path.join(dir, item.name);
    if (item.isDirectory()) {
      await walk(abs, base, out, limit);
      continue;
    }
    const ext = path.extname(item.name).toLowerCase();
    if (!IMAGE_EXT.has(ext) && !VIDEO_EXT.has(ext)) continue;
    const stat = await fs.promises.stat(abs);
    const rel = path.relative(base, abs).replace(/\\/g, "/");
    out.push({
      name: item.name,
      rel,
      url: assetUrl(rel),
      size: stat.size,
      kind: VIDEO_EXT.has(ext) ? "video" : "image",
    });
  }
}

const LIBRARY_FOLDERS = [
  "posters",
  "posters/custom",
  "videos",
  "storyboards",
  "backgrounds",
  "brand",
  "pages",
];

export async function library(kind?: string, limit = 800) {
  const folders = kind ? [kind] : LIBRARY_FOLDERS;
  const out: Record<string, Entry[]> = {};
  for (const folder of folders) {
    const base = path.join(ASSETS_DIR, folder);
    const entries: Entry[] = [];
    await walk(base, ASSETS_DIR, entries, limit);
    out[folder] = entries.sort((a, b) => a.rel.localeCompare(b.rel));
  }
  return out;
}

export async function runAudit(): Promise<StudioResult> {
  return runStudio(["audit.py"], 180000);
}

export async function runPosters(slug?: string, formats?: string[]): Promise<StudioResult> {
  const args = ["run_posters.py"];
  if (slug) args.push(slug);
  return runStudio(args, 600000);
}

export async function runVideo(spot: string): Promise<StudioResult> {
  return runStudio(["videos.py", spot], STUDIO_TIMEOUT_MS);
}

export async function runAds(spot: string): Promise<StudioResult> {
  return runStudio(["ads.py", spot], STUDIO_TIMEOUT_MS);
}

export function hasPython(): boolean {
  try {
    return fs.existsSync(PY);
  } catch {
    return false;
  }
}
