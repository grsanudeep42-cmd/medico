"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.redis_client import close_redis, get_redis
from app.routers import health
from app.routers.facilities import router as facilities_router
from app.routers.departments import router as departments_router
from app.routers.equipment import router as equipment_router
from app.routers.stock import router as stock_router
from app.routers.beds import router as beds_router
from app.routers.attendance import attendance_router, staff_router
from app.routers.footfall import router as footfall_router
from app.routers.ws import router as ws_router
from app.routers.ai import router as ai_router
from app.routers.alerts import router as alerts_router
from app.services.ai_scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Startup / shutdown lifecycle hooks."""
    # warm up redis connection
    get_redis()
    # start background AI scheduler (runs immediately + every 6 h)
    start_scheduler()
    yield
    # graceful shutdown
    stop_scheduler()
    await close_redis()


app = FastAPI(
    title="Medico API",
    version="0.1.0",
    description=(
        "Healthcare facility management API. "
        "Full CRUD on facilities, departments, equipment, stock levels, "
        "beds, attendance, and footfall — with live Redis pub/sub, WebSocket dashboards, "
        "and an autonomous AI scheduler that flags at-risk facilities."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(facilities_router)
app.include_router(departments_router)
app.include_router(equipment_router)
app.include_router(stock_router)
app.include_router(beds_router)
app.include_router(staff_router)
app.include_router(attendance_router)
app.include_router(footfall_router)
app.include_router(ws_router)
app.include_router(ai_router)
app.include_router(alerts_router)
