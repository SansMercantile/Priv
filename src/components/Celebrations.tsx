import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PartyPopper, X } from "lucide-react";
import { getAuthToken } from "../lib/authToken";

interface CelebrationEvent {
  type: string;
  milestone: number;
  profit_today: number;
  tone: "green" | "gold" | "platinum";
  message: string;
}

const TONE_STYLES: Record<string, string> = {
  green: "from-emerald-500/90 to-emerald-700/90 border-emerald-300/40",
  gold: "from-amber-400/90 to-amber-600/90 border-amber-200/40",
  platinum: "from-fuchsia-400/90 via-violet-500/90 to-indigo-600/90 border-fuchsia-200/40",
};

// Small deterministic-looking confetti burst using framer-motion, not a
// static image or a hardcoded "success" animation -- each piece's
// direction/rotation is randomized per celebration so it actually reads
// as a burst rather than the same GIF replaying.
function ConfettiBurst() {
  const pieces = useRef(
    Array.from({ length: 18 }, (_, i) => ({
      id: i,
      x: (Math.random() - 0.5) * 220,
      y: -Math.random() * 160 - 40,
      rotate: (Math.random() - 0.5) * 540,
      color: ["#34d399", "#fbbf24", "#f472b6", "#60a5fa", "#a78bfa"][i % 5],
      delay: Math.random() * 0.15,
    }))
  ).current;

  return (
    <div className="absolute inset-0 overflow-visible pointer-events-none">
      {pieces.map((p) => (
        <motion.span
          key={p.id}
          className="absolute left-1/2 top-1/2 w-1.5 h-3 rounded-sm"
          style={{ backgroundColor: p.color }}
          initial={{ opacity: 1, x: 0, y: 0, rotate: 0 }}
          animate={{ opacity: 0, x: p.x, y: p.y, rotate: p.rotate }}
          transition={{ duration: 1.1, delay: p.delay, ease: "easeOut" }}
        />
      ))}
    </div>
  );
}

export default function Celebrations() {
  const [queue, setQueue] = useState<CelebrationEvent[]>([]);
  const [current, setCurrent] = useState<CelebrationEvent | null>(null);
  const pollRef = useRef<number | null>(null);

  const poll = async () => {
    try {
      const token = await getAuthToken();
      if (!token) return; // celebrations require sign-in (real account data)
      const res = await fetch("/api/v1/support/celebrations", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const events: CelebrationEvent[] = data.celebrations || [];
      if (events.length > 0) {
        setQueue((prev) => [...prev, ...events]);
      }
    } catch {
      // Silent: this is a background nicety, never worth surfacing an error for.
    }
  };

  useEffect(() => {
    poll();
    pollRef.current = window.setInterval(poll, 30_000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  // Show one celebration at a time, in order, auto-dismissing after 6s.
  useEffect(() => {
    if (!current && queue.length > 0) {
      const [next, ...rest] = queue;
      setCurrent(next);
      setQueue(rest);
    }
  }, [queue, current]);

  useEffect(() => {
    if (!current) return;
    const t = window.setTimeout(() => setCurrent(null), 6000);
    return () => window.clearTimeout(t);
  }, [current]);

  return (
    <AnimatePresence>
      {current && (
        <motion.div
          key={`${current.type}-${current.milestone}`}
          className="fixed top-6 left-1/2 z-[9999] -translate-x-1/2"
          initial={{ opacity: 0, y: -40, scale: 0.85 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 22 }}
        >
          <div
            className={`relative overflow-visible bg-gradient-to-br ${TONE_STYLES[current.tone] || TONE_STYLES.green} border rounded-2xl shadow-2xl px-5 py-4 flex items-center gap-3 min-w-[280px]`}
          >
            <ConfettiBurst />
            <div className="relative flex-shrink-0 bg-white/15 rounded-full p-2">
              <PartyPopper className="w-5 h-5 text-white" />
            </div>
            <div className="relative flex-1 text-white">
              <p className="text-sm font-semibold leading-tight">{current.message}</p>
              <p className="text-xs text-white/70 mt-0.5">
                Today's profit: ${current.profit_today.toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => setCurrent(null)}
              className="relative flex-shrink-0 text-white/60 hover:text-white transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
