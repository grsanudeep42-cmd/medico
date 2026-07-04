"use client";

/**
 * FacilityMap — Leaflet map rendered only on the client (SSR disabled).
 * Shows a pin for each facility with a popup linking to the drilldown page.
 * Relies on lat/lng from the Facility record; facilities at (0,0) are skipped.
 */

import { useEffect, useRef } from "react";
import type { Facility } from "@/lib/types";

interface Props {
  facilities: Facility[];
}

export default function FacilityMap({ facilities }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);

  const positioned = facilities.filter(
    (f) => !(f.lat === 0 && f.lng === 0)
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (mapRef.current) return; // already initialised

    // Dynamic import to avoid SSR issues with Leaflet
    import("leaflet").then((L) => {
      if (!containerRef.current) return;

      // Fix default icon paths broken by webpack
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const defaultCenter: [number, number] =
        positioned.length > 0
          ? [positioned[0].lat, positioned[0].lng]
          : [20.5937, 78.9629]; // centre of India

      const map = L.map(containerRef.current!, {
        center: defaultCenter,
        zoom: positioned.length > 1 ? 7 : 12,
        zoomControl: true,
      });

      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
          maxZoom: 18,
        }
      ).addTo(map);

      for (const fac of positioned) {
        const popup = L.popup().setContent(`
          <div style="font-family:Inter,sans-serif;min-width:160px">
            <p style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin:0 0 2px">${fac.facility_id}</p>
            <p style="font-size:14px;font-weight:600;color:#e2e8f0;margin:0 0 6px">${fac.name}</p>
            <p style="font-size:12px;color:#64748b;margin:0 0 8px">${fac.address}</p>
            <a href="/facilities/${fac.id}" style="display:inline-block;background:#6366f1;color:#fff;font-size:11px;font-weight:600;padding:4px 10px;border-radius:6px;text-decoration:none">
              View details →
            </a>
          </div>
        `);

        L.marker([fac.lat, fac.lng])
          .bindPopup(popup)
          .addTo(map);
      }

      mapRef.current = map;
    });

    return () => {
      if (mapRef.current) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (mapRef.current as any).remove();
        mapRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (positioned.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/40 py-10 text-sm text-slate-500">
        Map unavailable — no facilities have valid coordinates (lat/lng ≠ 0)
      </div>
    );
  }

  return (
    <>
      {/* Leaflet CSS */}
      {/* eslint-disable-next-line @next/next/no-page-custom-font */}
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <div
        ref={containerRef}
        id="facility-map"
        className="h-72 w-full overflow-hidden rounded-xl border border-slate-700/50 shadow-lg"
      />
    </>
  );
}
