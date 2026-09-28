import React, { useState, useEffect } from "react";
import { Link2, Activity } from "lucide-react";
import apiClient from "../api/apiClient";
import Connections from "./Connections";
import DataIngestion from "./DataIngestion";

// SANS Network Link page shell: the existing connections view plus the
// Data Ingest framework as an in-page tab. Data Ingest is admin-only --
// the tab never renders for clients and the content is only mounted for
// admins (mirrors the old sidebar entry's visibility rule).
export default function ConnectionsSection({ demoMode }: { demoMode?: boolean }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [checked, setChecked] = useState(false);
  const [tab, setTab] = useState<"link" | "ingest">("link");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res: any = await apiClient.get("/api/v1/admin/whoami");
        if (!cancelled && res?.data?.data?.admin) setIsAdmin(true);
      } catch (_) {
        /* stay non-admin: no Data Ingest tab */
      } finally {
        if (!cancelled) setChecked(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Clients: render the plain page, no tab chrome at all.
  if (!checked) return <Connections demoMode={demoMode} />;
  if (!isAdmin) return <Connections demoMode={demoMode} />;

  return (
    <div className="space-y-4">
      <div className="flex border-b border-zinc-900 pb-3 gap-2 overflow-x-auto scrollbar-hide">
        {[
          { id: "link" as const, label: "Link Manager", icon: Link2 },
          { id: "ingest" as const, label: "Data Ingest", icon: Activity }
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
      {tab === "ingest" ? (
        <DataIngestion demoMode={demoMode} />
      ) : (
        <Connections demoMode={demoMode} />
      )}
    </div>
  );
}
