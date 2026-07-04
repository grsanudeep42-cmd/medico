"use client";

import type { WsFrame } from "@/lib/types";
import { useFacilityWs } from "@/lib/hooks/useFacilityWs";

const EVENT_COLORS: Record<string, string> = {
  "footfall.created": "bg-emerald-900/60 text-emerald-300 border-emerald-700/50",
  "footfall.updated": "bg-emerald-900/40 text-emerald-400 border-emerald-800/40",
  "bed.created": "bg-blue-900/60 text-blue-300 border-blue-700/50",
  "bed.updated": "bg-blue-900/40 text-blue-400 border-blue-800/40",
  "stock_level.created": "bg-amber-900/60 text-amber-300 border-amber-700/50",
  "stock_level.updated": "bg-amber-900/40 text-amber-400 border-amber-800/40",
  "attendance.created": "bg-violet-900/60 text-violet-300 border-violet-700/50",
  "attendance.updated": "bg-violet-900/40 text-violet-400 border-violet-800/40",
  "staff.created": "bg-pink-900/60 text-pink-300 border-pink-700/50",
  "facility.updated": "bg-indigo-900/60 text-indigo-300 border-indigo-700/50",
};

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

interface Props {
  facilityId: string;
}

export default function AlertsPanel({ facilityId }: Props) {
  const { frames, connected, error } = useFacilityWs(facilityId);

  const chipCls = (event: string) =>
    EVENT_COLORS[event] ??
    "bg-slate-700/60 text-slate-300 border-slate-600/50";

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-700/50 bg-slate-800/60 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/50 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-200">Live Events</h2>
        <span
          className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
            connected
              ? "bg-emerald-900/50 text-emerald-400"
              : error
              ? "bg-red-900/50 text-red-400"
              : "bg-slate-700/50 text-slate-400"
          }`}
        >
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              connected
                ? "bg-emerald-400 animate-pulse"
                : "bg-slate-500"
            }`}
          />
          {connected ? "Live" : error ? "Error" : "Connecting…"}
        </span>
      </div>

      {/* Event list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
        {frames.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              className="mb-3 h-8 w-8 text-slate-600"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"
              />
            </svg>
            <p className="text-xs text-slate-500">No live events yet</p>
            <p className="mt-1 text-[10px] text-slate-600">
              Events appear here when the facility data changes
            </p>
          </div>
        ) : (
          frames.map((frame) => (
            <FrameRow key={`${frame.receivedAt}-${frame.event}`} frame={frame} chipCls={chipCls} />
          ))
        )}
      </div>

      {error && (
        <div className="border-t border-slate-700/50 px-4 py-2">
          <p className="text-[10px] text-red-400">{error} — reconnecting…</p>
        </div>
      )}
    </div>
  );
}

function FrameRow({
  frame,
  chipCls,
}: {
  frame: WsFrame;
  chipCls: (e: string) => string;
}) {
  return (
    <div className="flex items-start gap-2 rounded-lg bg-slate-900/40 px-3 py-2">
      <span
        className={`mt-0.5 shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-mono font-medium ${chipCls(
          frame.event
        )}`}
      >
        {frame.event}
      </span>
      <span className="ml-auto shrink-0 text-[10px] text-slate-500 tabular-nums">
        {formatTime(frame.receivedAt)}
      </span>
    </div>
  );
}
