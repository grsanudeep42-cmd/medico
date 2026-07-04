"use client";

import type { StockLevel } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  data: StockLevel[];
}

interface ChartDatum {
  item: string;
  quantity: number;
  threshold: number;
  belowThreshold: boolean;
}

export default function StockChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No stock data loaded for this facility yet"
        message="Stock levels appear here once inventory items are created and quantities are recorded via the API or DVDMS upload."
      />
    );
  }

  const chartData: ChartDatum[] = data.slice(0, 20).map((row) => ({
    item: row.item_id.slice(0, 8), // abbreviated UUID as label until item names are joined
    quantity: row.quantity,
    threshold: row.reorder_threshold,
    belowThreshold: row.quantity <= row.reorder_threshold,
  }));

  // Shared max threshold reference line value (median threshold)
  const thresholds = chartData.map((d) => d.threshold).filter((t) => t > 0);
  const medianThreshold =
    thresholds.length > 0
      ? thresholds.sort((a, b) => a - b)[Math.floor(thresholds.length / 2)]
      : null;

  return (
    <div className="space-y-3">
      {chartData.some((d) => d.belowThreshold) && (
        <div className="flex items-center gap-2 rounded-lg border border-red-700/40 bg-red-900/20 px-3 py-2 text-xs text-red-300">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0">
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
              clipRule="evenodd"
            />
          </svg>
          {chartData.filter((d) => d.belowThreshold).length} item(s) below
          reorder threshold
        </div>
      )}

      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 8, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.6} horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            type="category"
            dataKey="item"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={70}
          />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
              fontSize: 12,
            }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: any, _name: any, props: any) => [
              `${value} units`,
              props.payload.belowThreshold ? "⚠ Below threshold" : "In stock",
            ]}
          />
          {medianThreshold !== null && (
            <ReferenceLine
              x={medianThreshold}
              stroke="#f59e0b"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{
                value: "Reorder",
                position: "insideTopRight",
                fill: "#f59e0b",
                fontSize: 10,
              }}
            />
          )}
          <Bar dataKey="quantity" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.belowThreshold ? "#ef4444" : "#6366f1"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
