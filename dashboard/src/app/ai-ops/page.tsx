"use client";

import React, { useEffect, useState } from "react";
import { getAiAnalytics, approveTransfer } from "@/lib/api";
import type { AiAnalyticsReport, TransferResult } from "@/lib/types";
import EmptyState from "@/components/EmptyState";

export default function AiOpsPage() {
  const [report, setReport] = useState<AiAnalyticsReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "flagged" | "forecast" | "redistribute">("all");
  const [transferStates, setTransferStates] = useState<Record<string, { loading: boolean; done: boolean; result?: TransferResult; error?: string }>>({});


  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAiAnalytics();
      setReport(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load AI analytics from backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveTransfer = async (
    recId: string,
    fromFacilityId: string,
    toFacilityId: string,
    itemId: string,
    quantity: number,
    reason: string
  ) => {
    setTransferStates(prev => ({
      ...prev,
      [recId]: { loading: true, done: false }
    }));
    try {
      const result = await approveTransfer({
        from_facility_id: fromFacilityId,
        to_facility_id: toFacilityId,
        item_id: itemId,
        quantity,
        recommendation_reason: reason,
      });
      setTransferStates(prev => ({
        ...prev,
        [recId]: { loading: false, done: true, result }
      }));
    } catch (err: unknown) {
      setTransferStates(prev => ({
        ...prev,
        [recId]: {
          loading: false,
          done: false,
          error: err instanceof Error ? err.message : "Transfer failed"
        }
      }));
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
        <p className="text-sm font-medium text-slate-400">Analyzing district healthcare metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-xl rounded-xl border border-red-700/50 bg-red-900/20 px-6 py-6 text-sm text-red-300">
        <div className="flex gap-3">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 text-red-400 shrink-0">
            <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-8-5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0v-4.5A.75.75 0 0 1 10 5Zm0 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="text-base font-semibold text-slate-100">AI Analytics Offline</h3>
            <p className="mt-1 leading-relaxed text-red-400">
              Could not fetch operational warnings from the backend. Please check if the FastAPI server is running and the database is seeded.
            </p>
            <button
              onClick={fetchReport}
              className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white hover:bg-red-500 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!report || report.facilities.length === 0) {
    return (
      <EmptyState
        title="No operational data available"
        message="Seed facilities and operational metrics in your database first to generate AI risk assessments and demand forecasts."
      />
    );
  }

  const { facilities, at_risk_facilities, demand_forecasts, redistribution_recommendations } = report;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-300 to-indigo-300">
            AI Operations Control Room
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time diagnostic auditing, stock-out forecasts, and automated resource redistribution recommendations.
          </p>
        </div>
        <button
          onClick={fetchReport}
          className="self-start flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white transition-all shadow-md active:scale-95"
        >
          <svg fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor" className="h-3.5 w-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh Audit
        </button>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="relative overflow-hidden rounded-2xl border border-red-500/20 bg-gradient-to-b from-red-500/5 to-red-500/0 p-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">At-Risk Facilities</span>
            <span className="flex h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
          </div>
          <p className="mt-2 text-4xl font-extrabold text-red-400">{at_risk_facilities.length}</p>
          <p className="mt-1 text-xs text-slate-500">Require immediate operational intervention</p>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-amber-500/20 bg-gradient-to-b from-amber-500/5 to-amber-500/0 p-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">Imminent Stock-outs</span>
            <span className="flex h-2.5 w-2.5 rounded-full bg-amber-500"></span>
          </div>
          <p className="mt-2 text-4xl font-extrabold text-amber-400">{demand_forecasts.length}</p>
          <p className="mt-1 text-xs text-slate-500">Items running out within 7 days</p>
        </div>

        <div className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-b from-indigo-500/5 to-indigo-500/0 p-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-400">Pending Redistributions</span>
            <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-500"></span>
          </div>
          <p className="mt-2 text-4xl font-extrabold text-indigo-400">{redistribution_recommendations.length}</p>
          <p className="mt-1 text-xs text-slate-500">Recommended resource optimization transfers</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab("all")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "all" ? "border-indigo-500 text-indigo-400 bg-indigo-950/10" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          All Facilities ({facilities.length})
        </button>
        <button
          onClick={() => setActiveTab("flagged")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "flagged" ? "border-red-500 text-red-400 bg-red-950/10" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Risk Flags ({at_risk_facilities.length})
        </button>
        <button
          onClick={() => setActiveTab("forecast")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "forecast" ? "border-amber-500 text-amber-400 bg-amber-950/10" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Demand Forecasts ({demand_forecasts.length})
        </button>
        <button
          onClick={() => setActiveTab("redistribute")}
          className={`px-5 py-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "redistribute" ? "border-indigo-500 text-indigo-400 bg-indigo-950/10" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Smart Redistribution ({redistribution_recommendations.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Tab 1 & 2: Facilities List / Flagged list */}
        {(activeTab === "all" || activeTab === "flagged") && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-4">Facility ID / Name</th>
                    <th className="px-6 py-4">Tier</th>
                    <th className="px-6 py-4">Stockouts</th>
                    <th className="px-6 py-4">Bed Volatility</th>
                    <th className="px-6 py-4">Doc Attendance</th>
                    <th className="px-6 py-4">Footfall / Med</th>
                    <th className="px-6 py-4">Test Gap</th>
                    <th className="px-6 py-4">Status / Indicators</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {(activeTab === "all" ? facilities : at_risk_facilities).map(fac => (
                    <tr key={fac.id} className="hover:bg-slate-800/35 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-200">{fac.name}</div>
                        <div className="text-xs text-slate-500">{fac.facility_id}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-400 uppercase">
                          {fac.tier}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={fac.stockout_frequency > 20 ? "text-red-400 font-semibold" : ""}>
                          {fac.stockout_frequency.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={fac.bed_volatility > 0.3 ? "text-red-400 font-semibold" : ""}>
                          {fac.bed_volatility.toFixed(3)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={fac.doctor_attendance < 80 ? "text-red-400 font-semibold" : ""}>
                          {fac.doctor_attendance.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={fac.footfall_vs_median < 0.5 ? "text-red-400 font-semibold" : ""}>
                          {fac.footfall_vs_median.toFixed(2)}x
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={fac.test_gap_percentage > 30 ? "text-red-400 font-semibold" : ""}>
                          {fac.test_gap_percentage.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {fac.flagged ? (
                          <div className="space-y-1">
                            <span className="inline-flex rounded-full bg-red-950/60 px-2.5 py-0.5 text-xs font-semibold text-red-400 border border-red-500/30">
                              ⚠️ RISK FLAG
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {fac.flagged_reasons.map((r, i) => (
                                <span key={i} className="rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                                  {r}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <span className="inline-flex rounded-full bg-emerald-950/60 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/30">
                            ✅ NORMAL
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Demand Forecasts */}
        {activeTab === "forecast" && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {demand_forecasts.length === 0 ? (
              <div className="md:col-span-2 text-center py-12 border border-slate-800 rounded-2xl text-slate-500">
                No inventory forecasting alerts. All medicine levels are stable.
              </div>
            ) : (
              demand_forecasts.map((fc, i) => (
                <div key={i} className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-base font-bold text-slate-200">{fc.item_name}</h4>
                        <p className="text-xs text-slate-500">{fc.facility_name}</p>
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                        fc.status === "critical" ? "bg-red-950 text-red-400 border border-red-500/20" : "bg-amber-950 text-amber-400 border border-amber-500/20"
                      }`}>
                        {fc.status}
                      </span>
                    </div>

                    <div className="mt-6 grid grid-cols-3 gap-2 text-center text-xs">
                      <div className="rounded-lg bg-slate-800/40 p-2.5">
                        <span className="block text-slate-500 font-medium">On Hand</span>
                        <span className="text-sm font-bold text-slate-200">{fc.quantity} units</span>
                      </div>
                      <div className="rounded-lg bg-slate-800/40 p-2.5">
                        <span className="block text-slate-500 font-medium">Threshold</span>
                        <span className="text-sm font-bold text-slate-200">{fc.reorder_threshold} units</span>
                      </div>
                      <div className="rounded-lg bg-slate-800/40 p-2.5">
                        <span className="block text-slate-500 font-medium">Daily Demand</span>
                        <span className="text-sm font-bold text-slate-200">{fc.daily_rate}/day</span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">Imminent Stock-out Risk</span>
                      <span className="font-semibold text-amber-400">{fc.days_remaining} days remaining</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${fc.status === "critical" ? "bg-red-500" : "bg-amber-500"}`}
                        style={{ width: `${Math.min((fc.days_remaining / 7) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 4: Redistribution Recommendations */}
        {activeTab === "redistribute" && (
          <div className="space-y-4">
            {redistribution_recommendations.length === 0 ? (
              <div className="text-center py-12 border border-slate-800 rounded-2xl text-slate-500">
                No pending resource transfers recommended.
              </div>
            ) : (
              redistribution_recommendations.map(rec => {
                const state = transferStates[rec.id];
                return (
                  <div key={rec.id} className="group overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between transition-all hover:border-indigo-500/40">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="rounded bg-indigo-950/60 px-2 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
                          Recommended transfer
                        </span>
                        <span className="text-xs text-slate-400 font-medium">
                          {rec.reason}
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-slate-200">
                        Transfer <span className="text-indigo-400 font-extrabold">{rec.recommended_quantity} units</span> of {rec.item_name}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span className="text-slate-300 font-semibold">{rec.from_facility_name}</span>
                        <span>➔</span>
                        <span className="text-slate-300 font-semibold">{rec.to_facility_name}</span>
                      </div>
                      {/* Show success or error messages inline */}
                      {state?.result && (
                        <p className="text-xs text-emerald-400 mt-1">{state.result.message}</p>
                      )}
                      {state?.error && (
                        <p className="text-xs text-red-400 mt-1">Error: {state.error}</p>
                      )}
                    </div>

                    <div className="self-end md:self-center shrink-0">
                      {state?.done ? (
                        <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-sm bg-emerald-950/30 border border-emerald-500/20 px-4 py-2 rounded-xl">
                          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                            <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
                          </svg>
                          Dispatched
                        </div>
                      ) : (
                        <button
                          onClick={() => handleApproveTransfer(
                            rec.id,
                            rec.from_facility_id,
                            rec.to_facility_id,
                            rec.item_id,
                            rec.recommended_quantity,
                            rec.reason
                          )}
                          disabled={state?.loading}
                          className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
                        >
                          {state?.loading ? (
                            <>
                              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                              Processing...
                            </>
                          ) : (
                            <>Approve Transfer</>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </div>
  );
}
