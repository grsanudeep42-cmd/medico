import React from "react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  message: string;
  className?: string;
}

/**
 * Rendered whenever a data array is empty. Never replaced by a sample chart.
 */
export default function EmptyState({
  icon,
  title = "No data loaded",
  message,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border border-slate-700/50 bg-slate-800/40 px-6 py-14 text-center ${className}`}
    >
      <div className="text-4xl opacity-40">
        {icon ?? (
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            className="h-12 w-12 text-slate-400"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 0 1 0 3.75H5.625a1.875 1.875 0 0 1 0-3.75Z"
            />
          </svg>
        )}
      </div>
      <p className="text-base font-semibold text-slate-300">{title}</p>
      <p className="max-w-xs text-sm leading-relaxed text-slate-500">
        {message}
      </p>
    </div>
  );
}
