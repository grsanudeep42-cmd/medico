"""ORM models package — import every module here so SQLAlchemy metadata and
Alembic autogenerate are aware of all tables.
"""

# Base mixins (no tables)
from app.models import base  # noqa: F401

# Domain models — import order follows FK dependency chain
from app.models.facility import Facility, FacilityTier, FacilityType  # noqa: F401
from app.models.department import Department  # noqa: F401
from app.models.equipment import Equipment  # noqa: F401
from app.models.daily_average import DailyAverage  # noqa: F401
from app.models.staff import AttendanceLog, Staff  # noqa: F401
from app.models.inventory import InventoryItem, StockLevel, StockTransaction, TransactionType  # noqa: F401
from app.models.bed import Bed  # noqa: F401
from app.models.footfall import FootfallLog  # noqa: F401
from app.models.test_availability import TestAvailability  # noqa: F401
from app.models.alert import FacilityAlert, AlertSeverity, AlertCategory  # noqa: F401

__all__ = [
    "Facility",
    "FacilityType",
    "FacilityTier",
    "Department",
    "Equipment",
    "DailyAverage",
    "Staff",
    "AttendanceLog",
    "InventoryItem",
    "StockLevel",
    "StockTransaction",
    "TransactionType",
    "Bed",
    "FootfallLog",
    "TestAvailability",
    "FacilityAlert",
    "AlertSeverity",
    "AlertCategory",
]
