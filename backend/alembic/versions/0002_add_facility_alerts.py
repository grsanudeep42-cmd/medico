"""Add facility_alerts table with enum types.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── Enum types (idempotent) ───────────────────────────────────────────────
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE alert_severity_enum AS ENUM ('info', 'warning', 'critical');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE alert_category_enum AS ENUM
                ('stockout', 'bed_volatility', 'doctor_attendance',
                 'footfall', 'diagnostic_gap', 'resource_redistribution');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    alert_severity_enum = postgresql.ENUM(
        "info", "warning", "critical",
        name="alert_severity_enum",
        create_type=False,
    )
    alert_category_enum = postgresql.ENUM(
        "stockout", "bed_volatility", "doctor_attendance",
        "footfall", "diagnostic_gap", "resource_redistribution",
        name="alert_category_enum",
        create_type=False,
    )

    # ── facility_alerts ───────────────────────────────────────────────────────
    op.create_table(
        "facility_alerts",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "facility_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("facilities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("facility_name", sa.Text(), nullable=False),
        sa.Column("severity", alert_severity_enum, nullable=False),
        sa.Column("category", alert_category_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_facility_alerts_facility_id", "facility_alerts", ["facility_id"])
    op.create_index("ix_facility_alerts_severity", "facility_alerts", ["severity"])
    op.create_index("ix_facility_alerts_category", "facility_alerts", ["category"])
    op.create_index("ix_facility_alerts_created_at", "facility_alerts", ["created_at"])
    # Index for fast unacknowledged query
    op.create_index(
        "ix_facility_alerts_unacked",
        "facility_alerts",
        ["acknowledged_at"],
    )


def downgrade() -> None:
    op.drop_table("facility_alerts")
    sa.Enum(name="alert_category_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="alert_severity_enum").drop(op.get_bind(), checkfirst=True)
