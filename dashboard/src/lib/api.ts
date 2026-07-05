/**
 * Thin fetch wrappers for every FastAPI endpoint used by the dashboard.
 *
 * All functions throw on non-2xx responses so callers can handle errors
 * centrally.  Server components can call these directly (no SWR needed).
 */

import type {
  AttendanceLog,
  BedSnapshot,
  Facility,
  FacilityAlert,
  FootfallLog,
  StockLevel,
  StockTransaction,
  StaffMember,
  AiAnalyticsReport,
  TransferApproveBody,
  TransferResult,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    // Always fetch fresh — this is a live operations dashboard
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API ${path} → ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API POST ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Facilities ────────────────────────────────────────────────────────────────

export const getFacilities = (): Promise<Facility[]> =>
  get<Facility[]>("/facilities");

export const getFacility = (id: string): Promise<Facility> =>
  get<Facility>(`/facilities/${id}`);

// ── Footfall ──────────────────────────────────────────────────────────────────

export const getFootfall = (facilityId: string): Promise<FootfallLog[]> =>
  get<FootfallLog[]>(`/facilities/${facilityId}/footfall?limit=365`);

// ── Beds ──────────────────────────────────────────────────────────────────────

export const getBeds = (facilityId: string): Promise<BedSnapshot[]> =>
  get<BedSnapshot[]>(`/facilities/${facilityId}/beds?limit=100`);

// ── Stock ─────────────────────────────────────────────────────────────────────

export const getStockLevels = (facilityId: string): Promise<StockLevel[]> =>
  get<StockLevel[]>(`/facilities/${facilityId}/stock-levels?limit=200`);

export const getStockTransactions = (
  facilityId: string
): Promise<StockTransaction[]> =>
  get<StockTransaction[]>(
    `/facilities/${facilityId}/stock-transactions?limit=200`
  );

// ── Staff & Attendance ────────────────────────────────────────────────────────

export const getStaff = (facilityId: string): Promise<StaffMember[]> =>
  get<StaffMember[]>(`/facilities/${facilityId}/staff?limit=200`);

export const getAttendance = (facilityId: string): Promise<AttendanceLog[]> =>
  get<AttendanceLog[]>(`/facilities/${facilityId}/attendance?limit=500`);

// ── WebSocket URL builders ────────────────────────────────────────────────────

export function buildWsUrl(facilityId: string): string {
  const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace(/^http/, "ws");
  return `${base}/ws/facility/${facilityId}`;
}

export function buildDistrictWsUrl(): string {
  const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    .replace(/^http/, "ws");
  return `${base}/ws/district`;
}

// ── AI Analytics ──────────────────────────────────────────────────────────────

export const getAiAnalytics = (): Promise<AiAnalyticsReport> =>
  get<AiAnalyticsReport>("/ai/analytics");

// ── Real stock transfer (replaces the old setTimeout mock) ────────────────────

export const approveTransfer = (body: TransferApproveBody): Promise<TransferResult> =>
  post<TransferResult>("/ai/transfers/approve", body);

// ── Alerts ────────────────────────────────────────────────────────────────────

export const getAlerts = (params?: {
  severity?: string;
  unacknowledged_only?: boolean;
  facility_id?: string;
  limit?: number;
}): Promise<FacilityAlert[]> => {
  const qs = new URLSearchParams();
  if (params?.severity) qs.set("severity", params.severity);
  if (params?.unacknowledged_only) qs.set("unacknowledged_only", "true");
  if (params?.facility_id) qs.set("facility_id", params.facility_id);
  if (params?.limit) qs.set("limit", String(params.limit));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return get<FacilityAlert[]>(`/alerts${query}`);
};

export const getUnreadAlertCount = (): Promise<{ count: number }> =>
  get<{ count: number }>("/alerts/unread-count");

export const acknowledgeAlert = (
  alertId: string,
  acknowledgedBy = "district_admin"
): Promise<FacilityAlert> =>
  post<FacilityAlert>(`/alerts/${alertId}/acknowledge`, {
    acknowledged_by: acknowledgedBy,
  });
