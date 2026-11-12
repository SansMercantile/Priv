import React, { useMemo, useState } from "react";
import {
  LifeBuoy,
  Search,
  BookOpen,
  HelpCircle,
  GraduationCap,
  ChevronDown,
  X,
  BadgeCheck,
} from "lucide-react";
import {
  FAQS,
  FAQ_CATEGORIES,
  GLOSSARY,
  TUTORIAL,
  searchHelp,
  FaqEntry,
} from "./helpContent";

// Help & Learn center: comprehensive tutorial + searchable FAQ + glossary.
// One page, three tabs, one search box that filters across ALL of it so a
// user can type any word and land on the answer / definition / step.

type Tab = "tutorial" | "faq" | "glossary";

const TAB_META: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "tutorial", label: "Tutorial", icon: GraduationCap },
  { id: "faq", label: "FAQ", icon: HelpCircle },
  { id: "glossary", label: "Glossary", icon: BookOpen },
];

function ScoreBadge({ score }: { score: number }) {
  const cls =
    score >= 80
      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"
      : score <= 20
      ? "bg-rose-500/15 text-rose-300 border-rose-500/40"
      : "bg-amber-500/10 text-amber-300 border-amber-500/30";
  return (
    <span className={`inline-block text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${cls}`}>
      {score}
    </span>
  );
}

function FaqItem({ entry, defaultOpen }: { entry: FaqEntry; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(!!defaultOpen);
  return (
    <div className="rounded-lg border border-white/10 bg-black/40 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-start justify-between gap-3 p-3 text-left hover:bg-white/5 transition"
      >
        <span className="text-sm text-white font-medium leading-snug">{entry.question}</span>
        <ChevronDown
          className={`w-4 h-4 shrink-0 text-zinc-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="px-3 pb-3 -mt-1">
          <p className="text-xs text-zinc-300 leading-relaxed font-light">{entry.answer}</p>
        </div>
      )}
    </div>
  );
}

export default function HelpCenter() {
  const [tab, setTab] = useState<Tab>("tutorial");
  const [query, setQuery] = useState("");
  const [faqCat, setFaqCat] = useState<string>("All");

  const results = useMemo(() => searchHelp(query), [query]);
  const searching = query.trim().length > 0;

  const faqs = useMemo(() => {
    if (faqCat === "All") return FAQS;
    return FAQS.filter((f) => f.category === faqCat);
  }, [faqCat]);

  const clearSearch = () => setQuery("");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-serif italic text-white flex items-center">
          <LifeBuoy className="w-8 h-8 mr-3 text-white/75" />
          Help &amp; Learn
        </h1>
        <p className="text-white/40 text-xs mt-1 font-light">
          Everything about signals, conviction scores, TP/SL, the autotrader and
          your account — searchable.
        </p>
      </div>

      {/* Search box */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder='Search anything… "score", "stop loss", "autotrader", "delivery", "verified"'
          className="w-full bg-black border border-white/15 rounded-xl pl-10 pr-10 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-white/40"
        />
        {searching && (
          <button
            onClick={clearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white"
            title="Clear search"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Search results (replace tabs while searching) */}
      {searching ? (
        <div className="space-y-3">
          <p className="text-xs font-mono text-zinc-500">
            {results.length} result{results.length === 1 ? "" : "s"} for “{query}”
          </p>
          {results.length === 0 && (
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-center">
              <p className="text-sm text-zinc-400">
                Nothing found. Try a different word — "score", "signal", "stop
                loss", "autotrader", "delivery", "tier", "verified".
              </p>
            </div>
          )}
          {results.map((r, i) => {
            if (r.kind === "faq") {
              return (
                <div key={`f-${r.entry.id}-${i}`}>
                  <span className="text-[9px] font-mono uppercase text-sky-400">FAQ · {r.entry.category}</span>
                  <FaqItem entry={r.entry} defaultOpen />
                </div>
              );
            }
            if (r.kind === "glossary") {
              return (
                <div key={`g-${r.entry.term}-${i}`} className="rounded-lg border border-white/10 bg-black/40 p-3">
                  <span className="text-[9px] font-mono uppercase text-violet-400">Glossary</span>
                  <div className="text-sm text-white font-semibold mt-0.5">{r.entry.term}</div>
                  <p className="text-xs text-zinc-300 mt-1 font-light">{r.entry.definition}</p>
                </div>
              );
            }
            return (
              <div key={`t-${r.entry.id}-${i}`} className="rounded-lg border border-white/10 bg-black/40 p-3">
                <span className="text-[9px] font-mono uppercase text-emerald-400">Tutorial</span>
                <div className="text-sm text-white font-semibold mt-0.5">{r.entry.title}</div>
                {r.entry.body.map((p, j) => (
                  <p key={j} className="text-xs text-zinc-300 mt-1.5 font-light leading-relaxed">
                    {p}
                  </p>
                ))}
              </div>
            );
          })}
        </div>
      ) : (
        <>
          {/* Tab bar */}
          <div className="flex gap-2 border-b border-white/10 pb-px">
            {TAB_META.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-4 py-2 text-xs font-mono uppercase tracking-wider border-b-2 transition ${
                  tab === id
                    ? "border-white text-white"
                    : "border-transparent text-zinc-500 hover:text-white"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {/* Tutorial tab */}
          {tab === "tutorial" && (
            <div className="space-y-4">
              {/* Score legend card */}
              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                <h2 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <BadgeCheck className="w-4 h-4 text-emerald-400" /> The one rule that matters
                </h2>
                <p className="text-xs text-zinc-300 font-light leading-relaxed">
                  Every signal and every autotrader trade carries a conviction
                  score from 0 to 100. We only act on <strong className="text-white">strong conviction</strong>:
                </p>
                <div className="flex flex-wrap items-center gap-3 mt-3 text-xs font-mono">
                  <span className="flex items-center gap-1.5">
                    <ScoreBadge score={85} /> strong bullish (≥80)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <ScoreBadge score={15} /> strong bearish (≤20)
                  </span>
                  <span className="flex items-center gap-1.5">
                    <ScoreBadge score={50} /> weak — never traded
                  </span>
                </div>
              </div>
              {TUTORIAL.map((step, idx) => (
                <div key={step.id} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="w-6 h-6 rounded-full bg-white/10 border border-white/20 text-white text-[11px] font-mono flex items-center justify-center">
                      {idx}
                    </span>
                    <h3 className="text-sm font-semibold text-white">{step.title}</h3>
                  </div>
                  {step.body.map((p, j) => (
                    <p key={j} className="text-xs text-zinc-300 font-light leading-relaxed mt-1.5 whitespace-pre-line">
                      {p}
                    </p>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* FAQ tab */}
          {tab === "faq" && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-1.5">
                {["All", ...FAQ_CATEGORIES].map((c) => (
                  <button
                    key={c}
                    onClick={() => setFaqCat(c)}
                    className={`px-2.5 py-1 rounded-full text-[10px] font-mono uppercase border transition ${
                      faqCat === c
                        ? "bg-white text-black border-white"
                        : "border-white/15 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              {faqs.map((entry) => (
                <FaqItem key={entry.id} entry={entry} />
              ))}
              {faqs.length === 0 && (
                <p className="text-xs text-zinc-500 font-mono">No questions in this category.</p>
              )}
            </div>
          )}

          {/* Glossary tab */}
          {tab === "glossary" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {GLOSSARY.map((g) => (
                <div key={g.term} className="rounded-lg border border-white/10 bg-black/40 p-3">
                  <div className="text-sm text-white font-semibold">{g.term}</div>
                  <p className="text-xs text-zinc-300 mt-1 font-light leading-relaxed">{g.definition}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
