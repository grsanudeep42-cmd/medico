/**
 * TypeScript interfaces mirroring the FastAPI / Pydantic schemas.
 * All field names match the snake_case convention used by the backend JSON.
 */

export type FacilityType = "PHC" | "CHC" | "tertiary_referral";
export type FacilityTier = "primary" | "community" | "apex";

export interface Facility {
  id: string;
  facility_id: string;
  name: string;
  facility_type: FacilityType;
  tier: FacilityTier;
  address: string;
  lat: number;
  lng: number;
  sanctioned_beds: number;
  functional_beds_estimate: number;
  referral_parent_id: string | null;
}

export interface FootfallLog {
  id: string;
  facility_id: string;
  date: string;          // ISO date string "YYYY-MM-DD"
  patient_count: number;
  department: string | null;
  is_simulated: boolean;
  basis: string;
}

export interface BedSnapshot {
  id: string;
  facility_id: string;
  total_beds: number;
  occupied_beds: number;
  updated_at: string;    // ISO datetime string
}

export interface StockLevel {
  id: string;
  facility_id: string;
  item_id: string;
  quantity: number;
  reorder_threshold: number;
  last_updated: string;
}

export type TransactionType =
  | "receipt"
  | "dispensed"
  | "adjustment"
  | "expired"
  | "transfer_in"
  | "transfer_out";

export interface StockTransaction {
  id: string;
  facility_id: string;
  item_id: string;
  delta: number;
  transaction_type: TransactionType;
  timestamp: string;
  is_simulated: boolean;
  basis: string;
}

export interface StaffMember {
  id: string;
  facility_id: string;
  role: string;
  name: string;
  sanctioned: boolean;
}

export interface AttendanceLog {
  id: string;
  staff_id: string;
  date: string;
  present: boolean;
  is_simulated: boolean;
  basis: string;
}

/** Envelope pushed over the WebSocket */
export interface WsFrame {
  event: string;         // e.g. "footfall.created", "ping"
  data?: Record<string, unknown>;
  receivedAt: number;    // client-assigned timestamp (Date.now())
}

// ── AI Analytics & Flagging ──────────────────────────────────────────────────

export interface FlaggedFacility {
  id: string;
  facility_id: string;
  name: string;
  tier: string;
  stockout_frequency: number;
  bed_volatility: number;
  doctor_attendance: number;
  footfall_vs_median: number;
  test_gap_percentage: number;
  flagged: boolean;
  flagged_reasons: string[];
}

export interface DemandForecast {
  facility_id: string;
  facility_name: string;
  item_id: string;
  item_name: string;
  category: string;
  quantity: number;
  reorder_threshold: number;
  days_remaining: number;
  daily_rate: number;
  status: "critical" | "warning";
}

export interface RedistributionRecommendation {
  id: string;
  from_facility_id: string;
  from_facility_name: string;
  to_facility_id: string;
  to_facility_name: string;
  item_id: string;
  item_name: string;
  recommended_quantity: number;
  reason: string;
}

export interface AiAnalyticsReport {
  overall_median_footfall: number;
  facilities: FlaggedFacility[];
  at_risk_facilities: FlaggedFacility[];
  demand_forecasts: DemandForecast[];
  redistribution_recommendations: RedistributionRecommendation[];
}

