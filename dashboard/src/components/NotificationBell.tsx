"use client";

/**
 * NotificationBell — real-time alert inbox for the district admin header.
 *
 * - Polls /alerts/unread-count on mount and after each acknowledge
 * - Connects to /ws/district so the count updates the instant the AI scheduler
 *   creates a new alert — no polling loop needed for live updates
 * - Clicking the bell opens an inbox panel showing the 20 most recent
 *   unacknowledged alerts
 * - Each alert has a real "Acknowledge" button that calls POST /alerts/{id}/acknowledge
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import type { FacilityAlert } from "@/lib/types";
import {
  acknowledgeAlert,
  buildDistrictWsUrl,
  getAlerts,
  getUnreadAlertCount,
} from "@/lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "border-red-500/40 bg-red-950/30",
  warning: "border-amber-500/40 bg-amber-950/30",
  info: "border-slate-600/40 bg-slate-800/30",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-600 text-white",
  warning: "bg-amber-500 text-slate-900",
  info: "bg-slate-600 text-slate-200",
};

const CATEGORY_LABELS: Record<string, string> = {
  stockout: "Stock-out",
  bed_volatility: "Bed Volatility",
  doctor_attendance: "Doctor Attendance",
  footfall: "Footfall",
  diagnostic_gap: "Diagnostic Gap",
  resource_redistribution: "Redistribution",
};

function timeAgo(isoString: string | null): string {
  if (!isoString) return "";
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [alerts, setAlerts] = useState<FacilityAlert[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);
  const [acknowledging, setAcknowledging] = useState<Set<string>>(new Set());
  const panelRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // ── Fetch unread count ──────────────────────────────────────────────────────
  const refreshCount = useCallback(async () => {
    try {
      const { count } = await getUnreadAlertCount();
      setUnreadCount(count);
    } catch {
      // Backend offline — silently ignore
    }
  }, []);

  // ── Fetch alert list (when panel opens) ────────────────────────────────────
  const loadAlerts = useCallback(async () => {
    setLoadingAlerts(true);
    try {
      const data = await getAlerts({ unacknowledged_only: true, limit: 20 });
      setAlerts(data);
    } catch {
      setAlerts([]);
    } finally {
      setLoadingAlerts(false);
    }
  }, []);

  // ── Connect to district WebSocket for live updates ─────────────────────────
  useEffect(() => {
    refreshCount();

    let ws: WebSocket;
    let retryTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        const url = buildDistrictWsUrl();
        ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onmessage = (evt) => {
          try {
            const frame = JSON.parse(evt.data as string);
            if (frame.event === "alert.created") {
              // Increment badge and refresh if panel is open
              setUnreadCount((c) => c + 1);
              setAlerts((prev) => {
                const newAlert: FacilityAlert = frame.data;
                // Avoid duplicates if we already have it
                if (prev.some((a) => a.id === newAlert.id)) return prev;
                return [newAlert, ...prev].slice(0, 20);
              });
            } else if (frame.event === "alert.acknowledged") {
              setUnreadCount((c) => Math.max(0, c - 1));
              setAlerts((prev) =>
                prev.filter((a) => a.id !== frame.data?.id)
              );
            }
            // Ignore "ping" frames
          } catch {
            // Ignore malformed frames
          }
        };

        ws.onclose = () => {
          // Reconnect after 5s if not deliberately closed
          retryTimeout = setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        retryTimeout = setTimeout(connect, 5000);
      }
    }

    connect();

    return () => {
      clearTimeout(retryTimeout);
      wsRef.current?.close();
    };
  }, [refreshCount]);

  // ── Open / close panel ─────────────────────────────────────────────────────
  useEffect(() => {
    if (open) {
      loadAlerts();
    }
  }, [open, loadAlerts]);

  // ── Close on outside click ─────────────────────────────────────────────────
  useEffect(() => {
    if (!open) return;
    function handler(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // ── Acknowledge a single alert ─────────────────────────────────────────────
  const handleAcknowledge = async (alertId: string) => {
    setAcknowledging((prev) => new Set(prev).add(alertId));
    try {
      await acknowledgeAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    } finally {
      setAcknowledging((prev) => {
        const next = new Set(prev);
        next.delete(alertId);
        return next;
      });
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        id="notification-bell"
        onClick={() => setOpen((o) => !o)}
        aria-label={`${unreadCount} unread alerts`}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-600 hover:text-slate-100 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
      >
        {/* Bell icon */}
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-4.5 w-4.5 h-[18px] w-[18px]"
        >
          <path
            fillRule="evenodd"
            d="M10 2a6 6 0 0 0-6 6c0 1.887-.454 3.665-1.257 5.234a.75.75 0 0 0 .515 1.076 32.91 32.91 0 0 0 3.256.508 3.5 3.5 0 0 0 6.972 0 32.903 32.903 0 0 0 3.256-.508.75.75 0 0 0 .515-1.076A11.448 11.448 0 0 1 16 8a6 6 0 0 0-6-6ZM8.05 14.943a33.54 33.54 0 0 0 3.9 0 2 2 0 0 1-3.9 0Z"
            clipRule="evenodd"
          />
        </svg>

        {/* Badge */}
        {unreadCount > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white leading-none shadow-lg shadow-red-500/30 animate-pulse">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 top-11 z-50 w-[420px] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl shadow-black/50 ring-1 ring-slate-800">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Operational Alerts
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {unreadCount > 0
                  ? `${unreadCount} unacknowledged`
                  : "All clear — no active alerts"}
              </p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-200 transition-colors"
            >
              <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </div>

          {/* Alert list */}
          <div className="max-h-[480px] overflow-y-auto">
            {loadingAlerts ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : alerts.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-500">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  className="mx-auto mb-3 h-10 w-10 text-slate-700"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                  />
                </svg>
                No active alerts
              </div>
            ) : (
              <ul className="divide-y divide-slate-800">
                {alerts.map((alert) => (
                  <li
                    key={alert.id}
                    className={`flex gap-3 px-4 py-3.5 transition-colors ${SEVERITY_COLORS[alert.severity] ?? ""}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${SEVERITY_BADGE[alert.severity]}`}
                        >
                          {alert.severity}
                        </span>
                        <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wide">
                          {CATEGORY_LABELS[alert.category] ?? alert.category}
                        </span>
                        <span className="ml-auto text-[10px] text-slate-600">
                          {timeAgo(alert.created_at)}
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-300">
                        {alert.message}
                      </p>
                    </div>
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={acknowledging.has(alert.id)}
                      title="Mark as acknowledged"
                      className="mt-0.5 shrink-0 flex h-7 w-7 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-400 hover:border-emerald-500/50 hover:bg-emerald-950/30 hover:text-emerald-400 transition-all disabled:opacity-40"
                    >
                      {acknowledging.has(alert.id) ? (
                        <div className="h-3 w-3 animate-spin rounded-full border border-slate-400 border-t-transparent" />
                      ) : (
                        <svg
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          className="h-3.5 w-3.5"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-slate-800 px-4 py-2.5">
            <a
              href="/ai-ops"
              onClick={() => setOpen(false)}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              View AI Control Room →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
