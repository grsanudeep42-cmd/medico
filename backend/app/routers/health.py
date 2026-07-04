"""Health-check router."""
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Return liveness status for Postgres and Redis."""
    # Postgres
    await db.execute(text("SELECT 1"))
    # Redis
    await redis.ping()
    return {"status": "ok", "postgres": "up", "redis": "up"}
