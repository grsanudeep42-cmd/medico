/**
 * / — Facility list page (server component).
 *
 * Fetches the live facility list from the FastAPI backend.
 * If the API is unreachable or the list is empty, shows explicit empty states.
 * No mock data. No placeholder cards.
 */
import type { Metadata } from "next";
import type { Facility } from "@/lib/types";
import { getFacilities } from "@/lib/api";
import FacilityCard from "@/components/FacilityCard";
import EmptyState from "@/components/EmptyState";
import FacilityMap from "@/components/FacilityMap";

export const metadata: Metadata = {
  title: "Facilities — Medico District Admin",
  description: "Browse all healthcare facilities in the district.",
};

// Revalidate every 60 s so the list stays fresh without a full reload
export const revalidate = 60;

export default async function FacilitiesPage() {
  let facilities: Facility[] = [];
  let fetchError: string | null = null;

  try {
    facilities = await getFacilities();
  } catch (err: unknown) {
    fetchError =
      err instanceof Error
        ? err.message
        : "Could not reach the Medico API. Is the backend running?";
  }

  const hasData = facilities.length > 0;

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-100">
          District Facilities
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Live operational overview of all facilities in the district.
        </p>
      </div>

      {/* API error banner */}
      {fetchError && (
        <div className="flex items-start gap-3 rounded-xl border border-red-700/50 bg-red-900/20 px-4 py-4 text-sm text-red-300">
          <svg
            viewBox="0 0 20 20"
            fill="currentColor"
            className="mt-0.5 h-5 w-5 shrink-0"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-8-5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0v-4.5A.75.75 0 0 1 10 5Zm0 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="font-medium">Backend unreachable</p>
            <p className="mt-0.5 text-xs text-red-400">{fetchError}</p>
          </div>
        </div>
      )}

      {/* Map view — only rendered when there are facilities with coordinates */}
      {hasData && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-500">
            Map
          </h2>
          <FacilityMap facilities={facilities} />
        </section>
      )}

      {/* Facility grid */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500">
            All Facilities
          </h2>
          {hasData && (
            <span className="rounded-full bg-indigo-900/40 px-2.5 py-0.5 text-xs font-medium text-indigo-300 border border-indigo-700/40">
              {facilities.length} facility{facilities.length !== 1 && "ies"}
            </span>
          )}
        </div>

        {!hasData && !fetchError ? (
          <EmptyState
            title="No facilities loaded yet"
            message="Run load_facility.py with a sourced facility JSON to seed your first facility. No data will appear until real records exist in the database."
          />
        ) : hasData ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {facilities.map((facility) => (
              <FacilityCard key={facility.id} facility={facility} />
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
