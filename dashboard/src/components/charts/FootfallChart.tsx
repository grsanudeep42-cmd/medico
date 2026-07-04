"use client";

import type { FootfallLog } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


interface Props {
  data: FootfallLog[];
}

interface ChartDatum {
  date: string;
  patients: number;
  simulated: boolean;
}

export default function FootfallChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No footfall data loaded for this facility yet"
        message="Run generate_logs.py (backed by real daily_averages) or upload field data to see patient count trends."
      />
    );
  }

  const chartData: ChartDatum[] = [...data]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((row) => ({
      date: row.date,
      patients: row.patient_count,
      simulated: row.is_simulated,
    }));

  const hasSimulated = chartData.some((d) => d.simulated);

  return (
    <div className="space-y-3">
      {hasSimulated && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-700/40 bg-amber-900/20 px-3 py-2 text-xs text-amber-300">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0">
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
              clipRule="evenodd"
            />
          </svg>
          Some data points are simulated (Poisson, anchored on real averages)
        </div>
      )}

      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="footfallGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.6} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: string) => v.slice(5)} // MM-DD
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
              fontSize: 12,
            }}
            labelStyle={{ color: "#94a3b8" }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(value: any) => [value ?? 0, "Patients"]}
          />
          <Area
            type="monotone"
            dataKey="patients"
            stroke="#6366f1"
            strokeWidth={2}
            fill="url(#footfallGrad)"
            dot={false}
            activeDot={{ r: 4, fill: "#818cf8" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
