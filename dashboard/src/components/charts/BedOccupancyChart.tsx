"use client";

import type { BedSnapshot } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  data: BedSnapshot[];
}

interface ChartDatum {
  time: string;
  occupied: number;
  free: number;
}

export default function BedOccupancyChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No bed occupancy data loaded for this facility yet"
        message="Bed snapshots appear here once field data or API writes populate the beds table."
      />
    );
  }

  const chartData: ChartDatum[] = [...data]
    .sort((a, b) => a.updated_at.localeCompare(b.updated_at))
    .slice(-30) // last 30 snapshots
    .map((row) => ({
      time: new Date(row.updated_at).toLocaleDateString([], {
        month: "short",
        day: "numeric",
      }),
      occupied: row.occupied_beds,
      free: Math.max(0, row.total_beds - row.occupied_beds),
    }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart
        data={chartData}
        margin={{ top: 4, right: 8, left: -10, bottom: 0 }}
        barCategoryGap="30%"
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.6} />
        <XAxis
          dataKey="time"
          tick={{ fill: "#64748b", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
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
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: "#94a3b8", paddingTop: 8 }}
        />
        <Bar dataKey="occupied" name="Occupied" fill="#6366f1" radius={[4, 4, 0, 0]} />
        <Bar dataKey="free" name="Free" fill="#1e3a5f" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
