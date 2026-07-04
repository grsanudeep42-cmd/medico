/**
 * /facilities/[id] — Per-facility drilldown page (server component).
 *
 * Fetches all metric data in parallel. Passes it as props to the client
 * DrilldownClient component which owns tabs, charts, and the WS panel.
 * Never falls back to placeholder data — all empty states are explicit.
 */
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getFacility,
  getFootfall,
  getBeds,
  getStockLevels,
  getAttendance,
} from "@/lib/api";
import DrilldownClient from "./DrilldownClient";

interface Props {
  params: { id: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const facility = await getFacility(params.id);
    return {
      title: `${facility.name} — Medico District Admin`,
      description: `Operational dashboard for ${facility.name} (${facility.facility_id}).`,
    };
  } catch {
    return { title: "Facility — Medico District Admin" };
  }
}

export const revalidate = 30;

export default async function FacilityDrilldownPage({ params }: Props) {
  // Facility 404 → use Next.js notFound()
  let facility;
  try {
    facility = await getFacility(params.id);
  } catch {
    notFound();
  }

  // Fetch all metrics in parallel; individual failures yield empty arrays
  const [footfall, beds, stockLevels, attendance] = await Promise.all([
    getFootfall(params.id).catch(() => []),
    getBeds(params.id).catch(() => []),
    getStockLevels(params.id).catch(() => []),
    getAttendance(params.id).catch(() => []),
  ]);

  const tierColors: Record<string, string> = {
    primary: "bg-emerald-900/50 text-emerald-300 border-emerald-700/50",
    community: "bg-blue-900/50 text-blue-300 border-blue-700/50",
    apex: "bg-violet-900/50 text-violet-300 border-violet-700/50",
  };
  const typeColors: Record<string, string> = {
    PHC: "bg-teal-900/40 text-teal-300 border-teal-700/40",
    CHC: "bg-cyan-900/40 text-cyan-300 border-cyan-700/40",
    tertiary_referral: "bg-indigo-900/40 text-indigo-300 border-indigo-700/40",
  };

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-slate-500">
        <Link href="/" className="hover:text-slate-300 transition-colors">
          Facilities
        </Link>
        <span>/</span>
        <span className="text-slate-300">{facility.name}</span>
      </nav>

      {/* Facility header */}
      <div className="flex flex-wrap items-start justify-between gap-4 rounded-xl border border-slate-700/50 bg-slate-800/60 p-6 shadow-lg">
        <div>
          <p className="font-mono text-[10px] tracking-widest text-slate-500 uppercase mb-1">
            {facility.facility_id}
          </p>
          <h1 className="text-2xl font-bold text-slate-100">{facility.name}</h1>
          <p className="mt-1 text-sm text-slate-500">{facility.address}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
              typeColors[facility.facility_type] ??
              "bg-slate-700/40 text-slate-300"
            }`}
          >
            {facility.facility_type.replace("_", " ")}
          </span>
          <span
            className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
              tierColors[facility.tier] ?? "bg-slate-700/40 text-slate-300"
            }`}
          >
            {facility.tier}
          </span>
        </div>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Sanctioned Beds", value: facility.sanctioned_beds },
          {
            label: "Functional Beds (est.)",
            value: facility.functional_beds_estimate,
          },
          { label: "Footfall Records", value: footfall.length },
          { label: "Stock Items", value: stockLevels.length },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="rounded-xl border border-slate-700/50 bg-slate-800/60 px-5 py-4"
          >
            <p className="text-[10px] font-medium uppercase tracking-widest text-slate-500">
              {label}
            </p>
            <p className="mt-1.5 text-2xl font-bold text-slate-100">{value}</p>
          </div>
        ))}
      </div>

      {/* Charts + Alerts — client island handles tabs & WS */}
      <DrilldownClient
        facilityId={params.id}
        footfall={footfall}
        beds={beds}
        stockLevels={stockLevels}
        attendance={attendance}
      />
    </div>
  );
}
