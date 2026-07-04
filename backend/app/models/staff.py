"""ORM models for facility staff members and their attendance logs."""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKey


class Staff(UUIDPrimaryKey, TimestampMixin, Base):
    """A staff member (sanctioned post or incumbent) at a facility."""

    __tablename__ = "staff"

    facility_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # e.g. "Medical Officer", "Staff Nurse", "ASHA Worker"
    role: Mapped[str] = mapped_column(Text, nullable=False)
    # True  → sanctioned post (may be vacant); False → contractual / ad-hoc
    sanctioned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    facility: Mapped["Facility"] = relationship(  # noqa: F821
        "Facility", back_populates="staff"
    )
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(
        "AttendanceLog", back_populates="staff_member", cascade="all, delete-orphan"
    )


class AttendanceLog(UUIDPrimaryKey, Base):
    """Daily attendance record for a staff member.

    Self-documenting provenance columns:
    - ``is_simulated`` — True if the record was model-generated, not field-verified.
    - ``basis``        — Human-readable explanation of how the record was produced
                         (e.g. "field HMIS upload 2024-06-01", "Monte-Carlo simulation v2").
    """

    __tablename__ = "attendance_logs"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Provenance
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    staff_member: Mapped["Staff"] = relationship("Staff", back_populates="attendance_logs")
