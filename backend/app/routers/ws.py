"""WebSocket endpoints for live dashboard pushes via Redis pub/sub.

Endpoints:
  GET /ws/facility/{facility_id}  — per-facility event stream
  GET /ws/district                — district-wide event stream (alerts from all facilities)

The client connects and receives a stream of JSON text frames, one per
Redis publish event on the subscribed channel.

Design decisions:
- A *dedicated* pubsub connection is created per WebSocket connection so
  that the main shared Redis client is not blocked on ``listen()``.
- ``asyncio.wait_for`` gives the receive-loop a heartbeat timeout so stale
  connections are detected quickly.
- Any exception during streaming results in a clean WebSocket close, not a
  server-side crash.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from app.config import settings
from app.services.publisher import _channel  # reuse channel-name helper

log = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# How long (seconds) to wait for a Redis message before looping again.
# Keeps the coroutine responsive to client disconnections.
_POLL_TIMEOUT: float = 5.0


async def _stream_channel(websocket: WebSocket, channel: str, label: str) -> None:
    """Shared WebSocket streaming loop for any Redis channel."""
    await websocket.accept()
    log.info("WebSocket opened for %s (channel: %s)", label, channel)

    pubsub_redis = Redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = pubsub_redis.pubsub()

    try:
        await pubsub.subscribe(channel)

        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=_POLL_TIMEOUT,
                )
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text('{"event":"ping"}')
                except WebSocketDisconnect:
                    break
                continue

            if message is None:
                await asyncio.sleep(0)
                continue

            if message["type"] == "message":
                try:
                    await websocket.send_text(message["data"])
                except WebSocketDisconnect:
                    break

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected for %s", label)
    except Exception as exc:  # noqa: BLE001
        log.warning("WebSocket error for %s: %s", label, exc)
    finally:
        try:
            await pubsub.unsubscribe(channel)
        except Exception:  # noqa: BLE001
            pass
        await pubsub_redis.aclose()
        log.info("WebSocket cleaned up for %s", label)


@router.websocket("/ws/facility/{facility_id}")
async def facility_ws(websocket: WebSocket, facility_id: str) -> None:
    """Stream live events for a single facility to a connected dashboard client."""
    await _stream_channel(websocket, _channel(facility_id), f"facility:{facility_id}")


@router.websocket("/ws/district")
async def district_ws(websocket: WebSocket) -> None:
    """Stream district-wide events (all alerts, transfers) to the notification bell."""
    await _stream_channel(websocket, _channel("district"), "district")

