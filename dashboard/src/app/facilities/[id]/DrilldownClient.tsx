"use client";

/**
 * DrilldownClient — client island for the facility drilldown page.
 *
 * Owns:
 *   - Tab strip (Footfall / Beds / Stock / Attendance)
 *   - Chart rendering per tab (with EmptyState guards)
 *   - AlertsPanel connected to the facility WebSocket
 *
 * Receives all data as props from the parent server component so no
 * client-side fetch is needed for initial render.
 */

import { useState } from "react";
import dynamic from "next/dynamic";
import AlertsPanel from "@/components/AlertsPanel";
import type {
  AttendanceLog,
  BedSnapshot,
  FootfallLog,
  StockLevel,
} from "@/lib/types";

// Dynamic imports to keep bundle lean and avoid Recharts SSR issues
const FootfallChart = dynamic(
  () => import("@/components/charts/FootfallChart"),
  { ssr: false }
);
const BedOccupancyChart = dynamic(
  () => import("@/components/charts/BedOccupancyChart"),
  { ssr: false }
);
const StockChart = dynamic(
  () => import("@/components/charts/StockChart"),
  { ssr: false }
);
const AttendanceChart = dynamic(
  () => import("@/components/charts/AttendanceChart"),
  { ssr: false }
);

type Tab = "footfall" | "beds" | "stock" | "attendance";

const TABS: { key: Tab; label: string }[] = [
  { key: "footfall", label: "Footfall" },
  { key: "beds", label: "Beds" },
  { key: "stock", label: "Stock" },
  { key: "attendance", label: "Attendance" },
];

interface Props {
  facilityId: string;
  footfall: FootfallLog[];
  beds: BedSnapshot[];
  stockLevels: StockLevel[];
  attendance: AttendanceLog[];
}

export default function DrilldownClient({
  facilityId,
  footfall,
  beds,
  stockLevels,
  attendance,
}: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("footfall");

  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-4">
      {/* ── Charts panel (3/4 width on xl) ─────────────────────────────── */}
      <div className="xl:col-span-3 space-y-0">
        {/* Tab strip */}
        <div className="flex gap-1 rounded-xl border border-slate-700/50 bg-slate-800/60 p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              id={`tab-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-150 ${
                activeTab === tab.key
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Chart area */}
        <div className="rounded-b-xl rounded-tr-xl border-x border-b border-slate-700/50 bg-slate-800/60 p-6 shadow-lg">
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-slate-200">
              {TABS.find((t) => t.key === activeTab)?.label} Overview
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {activeTab === "footfall" &&
                "Daily patient visits. Simulated rows are anchored on real published averages."}
              {activeTab === "beds" &&
                "Bed occupancy snapshots over time."}
              {activeTab === "stock" &&
                "Current on-hand quantities. Red bars are below the reorder threshold."}
              {activeTab === "attendance" &&
                "Daily staff presence grouped by date."}
            </p>
          </div>

          {activeTab === "footfall" && <FootfallChart data={footfall} />}
          {activeTab === "beds" && <BedOccupancyChart data={beds} />}
          {activeTab === "stock" && <StockChart data={stockLevels} />}
          {activeTab === "attendance" && <AttendanceChart data={attendance} />}
        </div>
      </div>

      {/* ── Alerts panel (1/4 width on xl) ──────────────────────────────── */}
      <div className="xl:col-span-1">
        <AlertsPanel facilityId={facilityId} />
      </div>
    </div>
  );
}
