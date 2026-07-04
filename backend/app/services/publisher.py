"""Redis pub/sub publisher helper.

Every write in the CRUD routers calls ``publish()`` to fan out a JSON event
on a per-facility channel:  medico:facility:{facility_id}
"""
from __future__ import annotations

import json
import logging
from typing import Any

from redis.asyncio import Redis

log = logging.getLogger(__name__)

CHANNEL_PREFIX = "medico:facility"


def _channel(facility_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{facility_id}"


async def publish(
    redis: Redis,
    facility_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """Publish a JSON event to the facility-scoped Redis channel.

    Errors are logged but never raised — a publish failure must never
    abort the HTTP response.
    """
    message = json.dumps(
        {"event": event_type, "facility_id": facility_id, "data": payload},
        default=str,   # handles UUID, datetime, Decimal
    )
    try:
        await redis.publish(_channel(facility_id), message)
    except Exception as exc:  # noqa: BLE001
        log.warning("Redis publish failed for facility %s: %s", facility_id, exc)
