"use client";

/**
 * useFacilityWs — subscribes to /ws/facility/{facilityId} and exposes
 * the latest received WsFrame plus the full event history (capped at 50).
 *
 * Reconnects automatically with exponential back-off (max 30 s) whenever
 * the connection drops unexpectedly. Cleans up on unmount.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { buildWsUrl } from "../api";
import type { WsFrame } from "../types";

const MAX_HISTORY = 50;
const BACKOFF_BASE_MS = 1_000;
const BACKOFF_MAX_MS = 30_000;

interface WsState {
  frames: WsFrame[];
  lastFrame: WsFrame | null;
  connected: boolean;
  error: string | null;
}

export function useFacilityWs(facilityId: string): WsState {
  const [state, setState] = useState<WsState>({
    frames: [],
    lastFrame: null,
    connected: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const url = buildWsUrl(facilityId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      attemptRef.current = 0;
      setState((s) => ({ ...s, connected: true, error: null }));
    };

    ws.onmessage = (ev) => {
      if (!mountedRef.current) return;
      try {
        const payload = JSON.parse(ev.data as string);
        // Skip keep-alive pings from the server
        if (payload.event === "ping") return;

        const frame: WsFrame = {
          event: payload.event ?? "unknown",
          data: payload.data,
          receivedAt: Date.now(),
        };

        setState((s) => {
          const frames = [frame, ...s.frames].slice(0, MAX_HISTORY);
          return { ...s, frames, lastFrame: frame };
        });
      } catch {
        // Malformed frame — ignore silently
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setState((s) => ({
        ...s,
        connected: false,
        error: "WebSocket connection error",
      }));
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setState((s) => ({ ...s, connected: false }));

      // Exponential back-off reconnect
      const delay = Math.min(
        BACKOFF_BASE_MS * 2 ** attemptRef.current,
        BACKOFF_MAX_MS
      );
      attemptRef.current += 1;
      retryRef.current = setTimeout(connect, delay);
    };
  }, [facilityId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return state;
}
