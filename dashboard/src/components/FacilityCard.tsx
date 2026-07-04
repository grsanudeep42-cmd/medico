import type { Facility } from "@/lib/types";
import Link from "next/link";

const TIER_COLORS: Record<string, string> = {
  primary: "bg-emerald-900/50 text-emerald-300 border-emerald-700/50",
  community: "bg-blue-900/50 text-blue-300 border-blue-700/50",
  apex: "bg-violet-900/50 text-violet-300 border-violet-700/50",
};

const TYPE_COLORS: Record<string, string> = {
  PHC: "bg-teal-900/40 text-teal-300 border-teal-700/40",
  CHC: "bg-cyan-900/40 text-cyan-300 border-cyan-700/40",
  tertiary_referral: "bg-indigo-900/40 text-indigo-300 border-indigo-700/40",
};

interface Props {
  facility: Facility;
}

export default function FacilityCard({ facility }: Props) {
  const tierCls =
    TIER_COLORS[facility.tier] ?? "bg-slate-700/40 text-slate-300";
  const typeCls =
    TYPE_COLORS[facility.facility_type] ?? "bg-slate-700/40 text-slate-300";

  const occupancyPct =
    facility.sanctioned_beds > 0
      ? Math.round(
          (facility.functional_beds_estimate / facility.sanctioned_beds) * 100
        )
      : null;

  return (
    <Link
      href={`/facilities/${facility.id}`}
      className="group block rounded-xl border border-slate-700/50 bg-slate-800/60 p-5 shadow-lg transition-all duration-200 hover:border-indigo-500/60 hover:bg-slate-800 hover:shadow-indigo-500/10 hover:shadow-xl"
    >
      {/* Header */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-mono tracking-widest text-slate-500 uppercase">
            {facility.facility_id}
          </p>
          <h3 className="mt-0.5 text-base font-semibold text-slate-100 group-hover:text-indigo-300 transition-colors">
            {facility.name}
          </h3>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${typeCls}`}
        >
          {facility.facility_type.replace("_", " ")}
        </span>
      </div>

      {/* Address */}
      <p className="mb-4 flex items-center gap-1.5 text-xs text-slate-500">
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-3.5 w-3.5 shrink-0"
        >
          <path
            fillRule="evenodd"
            d="M9.69 18.933l.003.001C9.89 19.02 10 19 10 19s.11.02.308-.066l.002-.001.006-.003.018-.008a5.741 5.741 0 0 0 .281-.14c.186-.096.446-.24.757-.433.62-.384 1.445-.966 2.274-1.765C15.302 14.988 17 12.493 17 9A7 7 0 1 0 3 9c0 3.492 1.698 5.988 3.355 7.584a13.731 13.731 0 0 0 2.273 1.765 11.842 11.842 0 0 0 .976.544l.062.029.018.008.006.003ZM10 11.25a2.25 2.25 0 1 0 0-4.5 2.25 2.25 0 0 0 0 4.5Z"
            clipRule="evenodd"
          />
        </svg>
        <span className="truncate">{facility.address}</span>
      </p>

      {/* Footer metrics */}
      <div className="flex items-center justify-between">
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider ${tierCls}`}
        >
          {facility.tier}
        </span>

        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>
            <span className="font-semibold text-slate-200">
              {facility.sanctioned_beds}
            </span>{" "}
            beds
          </span>
          {occupancyPct !== null && (
            <span className="text-slate-500">·</span>
          )}
          {occupancyPct !== null && (
            <span>
              <span className="font-semibold text-slate-200">
                {occupancyPct}%
              </span>{" "}
              functional
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
