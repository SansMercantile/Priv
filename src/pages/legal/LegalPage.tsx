import { useEffect, type ReactNode } from "react";
import { Link } from "react-router-dom";

/**
 * Shared shell for the /legal/* pages. These used to be six standalone
 * .html files under public/legal/ with their own <head> (a different
 * favicon, a stylesheet/logo that didn't exist post-deploy, no title
 * synced with the app). Moving them into the React app means they now
 * automatically get the real favicon and font/theme from index.html and
 * global CSS -- there is nothing page-specific left to configure for
 * that part, which is the whole point of this move.
 */
export default function LegalPage({
  title,
  updated,
  children,
}: {
  title: string;
  updated?: string;
  children: ReactNode;
}) {
  useEffect(() => {
    document.title = `${title} — Priv | Sans Mercantile`;
  }, [title]);

  return (
    <div className="min-h-screen bg-black text-white neural-grid matrix-bg">
      <header className="max-w-3xl mx-auto flex items-center justify-between px-4 sm:px-6 py-5">
        <Link to="/" className="flex items-center gap-2.5">
          <svg viewBox="0 0 100 100" fill="none" className="w-6 h-6">
            <defs>
              <linearGradient id="priv-g-legal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ff4b72" />
                <stop offset="50%" stopColor="#e11d48" />
                <stop offset="100%" stopColor="#9f1239" />
              </linearGradient>
            </defs>
            <path d="M50 15 L85 50 L50 85 L15 50 Z" stroke="url(#priv-g-legal)" strokeWidth="6" strokeLinejoin="round" />
            <path d="M50 28 L72 50 L50 72 L28 50 Z" fill="url(#priv-g-legal)" opacity="0.35" />
          </svg>
          <span className="text-sm font-semibold tracking-tight">Priv</span>
        </Link>
        <Link to="/" className="text-xs text-white/45 hover:text-white/90 transition-colors">
          ← Back to Priv
        </Link>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 pb-24">
        <div className="border-b border-white/5 pb-6 mb-8">
          <h1 className="text-2xl sm:text-3xl font-serif italic text-white">{title}</h1>
          {updated && <p className="text-xs text-white/40 mt-2">Last updated: {updated}</p>}
        </div>

        <div className="legal-body space-y-8 text-[15px] leading-relaxed text-white/70">
          {children}
        </div>
      </main>

      <footer className="border-t border-white/5">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row justify-between gap-4">
          <p className="text-[13px] text-white/40">A Sans Mercantile fintech product</p>
          <p className="text-xs text-white/30">© 2026 Sans Mercantile. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

/** Shared building blocks so each page's content reads as plain markup
 * instead of re-declaring className soup six times over. */
export function H2({ children }: { children: ReactNode }) {
  return <h2 className="text-lg font-semibold text-white mt-2">{children}</h2>;
}
export function H3({ children }: { children: ReactNode }) {
  return <h3 className="text-[15px] font-semibold text-white/90">{children}</h3>;
}
export function P({ children }: { children: ReactNode }) {
  return <p>{children}</p>;
}
export function UL({ children }: { children: ReactNode }) {
  return <ul className="list-disc pl-5 space-y-1.5 marker:text-white/30">{children}</ul>;
}
export function OL({ children }: { children: ReactNode }) {
  return <ol className="list-decimal pl-5 space-y-1.5 marker:text-white/30">{children}</ol>;
}
export function Section({ children }: { children: ReactNode }) {
  return <section className="space-y-3">{children}</section>;
}
