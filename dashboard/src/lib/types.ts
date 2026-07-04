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
