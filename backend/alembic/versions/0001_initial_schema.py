"""Initial schema — all domain tables.

Revision ID: 0001
Revises: (none)
Create Date: 2026-07-04

Tables created (in FK-dependency order):
    facilities, departments, equipment, daily_averages,
    staff, attendance_logs,
    inventory_items, stock_levels, stock_transactions,
    beds, footfall_logs, test_availability

Every operational log table carries ``is_simulated`` + ``basis`` so the DB is
self-documenting about what is real vs. modelled data.
No seed data is inserted — schema only.
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

# ── Revision identifiers ───────────────────────────────────────────────────────
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid_pk() -> sa.Column:
    """Standard UUID primary-key column."""
    return sa.Column(
        "id",
        sa.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


def _timestamps() -> list[sa.Column]:
    """created_at / updated_at columns present on most tables."""
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def _provenance() -> list[sa.Column]:
    """is_simulated + basis columns for operational log tables."""
    return [
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("basis", sa.Text(), nullable=False),
    ]


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ── Custom Postgres enum types ─────────────────────────────────────────────
    facility_type_enum = sa.Enum(
        "PHC", "CHC", "tertiary_referral",
        name="facility_type_enum",
    )
    facility_tier_enum = sa.Enum(
        "primary", "community", "apex",
        name="facility_tier_enum",
    )
    transaction_type_enum = sa.Enum(
        "receipt", "dispensed", "adjustment",
        "expired", "transfer_in", "transfer_out",
        name="transaction_type_enum",
    )
    facility_type_enum.create(op.get_bind(), checkfirst=True)
    facility_tier_enum.create(op.get_bind(), checkfirst=True)
    transaction_type_enum.create(op.get_bind(), checkfirst=True)

    # ── facilities ─────────────────────────────────────────────────────────────
    op.create_table(
        "facilities",
        _uuid_pk(),
        sa.Column("facility_id", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("facility_type", facility_type_enum, nullable=False),
        sa.Column("tier", facility_tier_enum, nullable=False),
        # Self-referential FK — added after table creation (see below)
        sa.Column("referral_parent_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("lat", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("lng", sa.Numeric(precision=10, scale=7), nullable=False),
        sa.Column("sanctioned_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "functional_beds_estimate", sa.Integer(), nullable=False, server_default="0"
        ),
        *_timestamps(),
    )
    op.create_unique_constraint(
        "uq_facilities_facility_id", "facilities", ["facility_id"]
    )
    op.create_index("ix_facilities_referral_parent_id", "facilities", ["referral_parent_id"])
    # Self-referential FK added now that the table exists
    op.create_foreign_key(
        "fk_facilities_referral_parent_id",
        "facilities",
        "facilities",
        ["referral_parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── departments ────────────────────────────────────────────────────────────
    op.create_table(
        "departments",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_departments_facility_id", "departments", ["facility_id"])

    # ── equipment ──────────────────────────────────────────────────────────────
    op.create_table(
        "equipment",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_equipment_facility_id", "equipment", ["facility_id"])

    # ── daily_averages ─────────────────────────────────────────────────────────
    # source_url is NOT NULL — every row must cite a published source.
    op.create_table(
        "daily_averages",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.Text(), nullable=False),
        sa.Column("avg_value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("min_value", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("max_value", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),          # mandatory citation
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_daily_averages_facility_id", "daily_averages", ["facility_id"])
    op.create_index("ix_daily_averages_metric_name", "daily_averages", ["metric_name"])
    op.create_index("ix_daily_averages_recorded_at", "daily_averages", ["recorded_at"])

    # ── staff ──────────────────────────────────────────────────────────────────
    op.create_table(
        "staff",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("sanctioned", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("name", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_staff_facility_id", "staff", ["facility_id"])

    # ── attendance_logs ────────────────────────────────────────────────────────
    op.create_table(
        "attendance_logs",
        _uuid_pk(),
        sa.Column(
            "staff_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("staff.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False),
        *_provenance(),
    )
    op.create_index("ix_attendance_logs_staff_id", "attendance_logs", ["staff_id"])
    op.create_index("ix_attendance_logs_date", "attendance_logs", ["date"])

    # ── inventory_items ────────────────────────────────────────────────────────
    op.create_table(
        "inventory_items",
        _uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_inventory_items_category", "inventory_items", ["category"])

    # ── stock_levels ───────────────────────────────────────────────────────────
    op.create_table(
        "stock_levels",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "quantity", sa.Numeric(precision=12, scale=3), nullable=False, server_default="0"
        ),
        sa.Column(
            "reorder_threshold",
            sa.Numeric(precision=12, scale=3),
            nullable=False,
            server_default="0",
        ),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stock_levels_facility_id", "stock_levels", ["facility_id"])
    op.create_index("ix_stock_levels_item_id", "stock_levels", ["item_id"])

    # ── stock_transactions ─────────────────────────────────────────────────────
    op.create_table(
        "stock_transactions",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delta", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        *_provenance(),
    )
    op.create_index(
        "ix_stock_transactions_facility_id", "stock_transactions", ["facility_id"]
    )
    op.create_index("ix_stock_transactions_item_id", "stock_transactions", ["item_id"])
    op.create_index("ix_stock_transactions_timestamp", "stock_transactions", ["timestamp"])

    # ── beds ───────────────────────────────────────────────────────────────────
    op.create_table(
        "beds",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("occupied_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_beds_facility_id", "beds", ["facility_id"])
    op.create_index("ix_beds_updated_at", "beds", ["updated_at"])

    # ── footfall_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "footfall_logs",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("patient_count", sa.Integer(), nullable=False),
        sa.Column("department", sa.Text(), nullable=True),  # NULL = whole-facility count
        *_provenance(),
    )
    op.create_index("ix_footfall_logs_facility_id", "footfall_logs", ["facility_id"])
    op.create_index("ix_footfall_logs_date", "footfall_logs", ["date"])

    # ── test_availability ──────────────────────────────────────────────────────
    op.create_table(
        "test_availability",
        _uuid_pk(),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("test_name", sa.Text(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_test_availability_facility_id", "test_availability", ["facility_id"]
    )
    op.create_index(
        "ix_test_availability_test_name", "test_availability", ["test_name"]
    )
    op.create_index(
        "ix_test_availability_last_checked", "test_availability", ["last_checked"]
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("test_availability")
    op.drop_table("footfall_logs")
    op.drop_table("beds")
    op.drop_table("stock_transactions")
    op.drop_table("stock_levels")
    op.drop_table("inventory_items")
    op.drop_table("attendance_logs")
    op.drop_table("staff")
    op.drop_table("daily_averages")
    op.drop_table("equipment")
    op.drop_table("departments")

    # Drop self-referential FK before the table itself
    op.drop_constraint("fk_facilities_referral_parent_id", "facilities", type_="foreignkey")
    op.drop_table("facilities")

    # Drop custom enum types
    sa.Enum(name="transaction_type_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="facility_tier_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="facility_type_enum").drop(op.get_bind(), checkfirst=True)
