"""ORM model for healthcare facilities (PHC / CHC / tertiary referral)."""
import enum
import uuid
from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class FacilityType(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"
    tertiary_referral = "tertiary_referral"


class FacilityTier(str, enum.Enum):
    primary = "primary"
    community = "community"
    apex = "apex"


class Facility(UUIDPrimaryKey, TimestampMixin, Base):
    """A physical healthcare facility in the referral hierarchy."""

    __tablename__ = "facilities"
    __table_args__ = (UniqueConstraint("facility_id", name="uq_facilities_facility_id"),)

    # Human-readable external identifier (e.g. "MH-PHC-0042")
    facility_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    facility_type: Mapped[FacilityType] = mapped_column(
        SAEnum(FacilityType, name="facility_type_enum", create_type=True), nullable=False
    )
    tier: Mapped[FacilityTier] = mapped_column(
        SAEnum(FacilityTier, name="facility_tier_enum", create_type=True), nullable=False
    )

    # Self-referential FK — NULL for apex facilities
    referral_parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("facilities.id", ondelete="SET NULL"), nullable=True, index=True
    )

    address: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(Numeric(precision=10, scale=7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(precision=10, scale=7), nullable=False)

    sanctioned_beds: Mapped[int] = mapped_column(nullable=False, default=0)
    # Functional estimate may differ from sanctioned; can be updated from field data
    functional_beds_estimate: Mapped[int] = mapped_column(nullable=False, default=0)

    # ── Relationships ──────────────────────────────────────────────────────────
    referral_parent: Mapped[Optional["Facility"]] = relationship(
        "Facility",
        back_populates="referral_children",
        remote_side="Facility.id",
        foreign_keys=[referral_parent_id],
    )
    referral_children: Mapped[list["Facility"]] = relationship(
        "Facility",
        back_populates="referral_parent",
        foreign_keys=[referral_parent_id],
    )

    departments: Mapped[list["Department"]] = relationship(  # noqa: F821
        "Department", back_populates="facility", cascade="all, delete-orphan"
    )
    equipment: Mapped[list["Equipment"]] = relationship(  # noqa: F821
        "Equipment", back_populates="facility", cascade="all, delete-orphan"
    )
    daily_averages: Mapped[list["DailyAverage"]] = relationship(  # noqa: F821
        "DailyAverage", back_populates="facility", cascade="all, delete-orphan"
    )
    staff: Mapped[list["Staff"]] = relationship(  # noqa: F821
        "Staff", back_populates="facility", cascade="all, delete-orphan"
    )
    stock_levels: Mapped[list["StockLevel"]] = relationship(  # noqa: F821
        "StockLevel", back_populates="facility", cascade="all, delete-orphan"
    )
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(  # noqa: F821
        "StockTransaction", back_populates="facility", cascade="all, delete-orphan"
    )
    beds: Mapped[list["Bed"]] = relationship(  # noqa: F821
        "Bed", back_populates="facility", cascade="all, delete-orphan"
    )
    footfall_logs: Mapped[list["FootfallLog"]] = relationship(  # noqa: F821
        "FootfallLog", back_populates="facility", cascade="all, delete-orphan"
    )
    test_availabilities: Mapped[list["TestAvailability"]] = relationship(  # noqa: F821
        "TestAvailability", back_populates="facility", cascade="all, delete-orphan"
    )
