import React, { useState } from "react";
import { Workflow, FlaskConical } from "lucide-react";
import { AutomationAutonomy } from "./AutomationAutonomy";
import StrategyTester from "./StrategyTester";

interface AutomationProps {
  demoMode?: boolean;
}

// Strategies page shell (sidebar: "Strategies", paid tiers only via
// RequirePaying): the existing Automation & Agent Orchestration view
// plus the new Strategy Tester, side by side as tabs.
export default function Automation({ demoMode }: AutomationProps) {
  const [tab, setTab] = useState<"orchestration" | "tester">("orchestration");

  return (
    <div className="space-y-4">
      <div className="flex border-b border-zinc-900 pb-3 gap-2 overflow-x-auto scrollbar-hide">
        {[
          { id: "orchestration" as const, label: "Automation & Agent Orchestration", icon: Workflow },
          { id: "tester" as const, label: "Strategy Tester", icon: FlaskConical }
        ].map((t) => {
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
      {tab === "orchestration" ? <AutomationAutonomy /> : <StrategyTester />}
    </div>
  );
}
