"""
generate_logs.py — Generate simulated daily footfall logs grounded in real
                   published averages stored in the ``daily_averages`` table.

Rules (never violated):
  1. If a facility has NO rows in ``daily_averages``, it is skipped entirely
     with a WARNING — no invented numbers are ever written.
  2. Every written row carries ``is_simulated=True`` and
     ``basis="real_average:<source_url>"`` so the provenance chain is intact.
  3. Patient counts are sampled from a Poisson distribution whose λ = the
     stored ``avg_value`` for the ``outpatient_visits`` metric, optionally
     scaled by a day-of-week multiplier that is configurable per facility_type.

CLI::

    # Generate 90 days for all facilities
    python generate_logs.py --days 90

    # Preview only — print what would be written without committing
    python generate_logs.py --days 30 --dry-run

    # Custom multipliers config file
    python generate_logs.py --days 60 --dow-config path/to/dow_config.json

Day-of-week multiplier JSON format::

    {
      "PHC":               [0.80, 1.00, 1.05, 1.05, 1.00, 0.70, 0.40],
      "CHC":               [0.85, 1.00, 1.05, 1.05, 1.00, 0.75, 0.50],
      "tertiary_referral": [0.90, 1.00, 1.02, 1.02, 1.00, 0.85, 0.70]
    }

Index 0 = Monday … 6 = Sunday (Python weekday() convention).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# ─── Path bootstrap — reuse backend ORM models ───────────────────────────────
backend_dir = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(backend_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("generate_logs")

# ─── Load .env before touching app imports ────────────────────────────────────
from dotenv import load_dotenv  # noqa: E402 — intentional post-path-setup

_env_loaded = False
for _search in [Path("."), Path(".."), Path("../.."), backend_dir]:
    _env_path = _search / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        _env_loaded = True
        logger.info("Loaded environment from %s", _env_path.resolve())
        break

if not _env_loaded:
    logger.warning("No .env file found; relying on existing environment variables.")

# ─── App imports (safe now that .env is loaded) ───────────────────────────────
import numpy as np  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

from app.models.facility import Facility, FacilityType  # noqa: E402
from app.models.daily_average import DailyAverage  # noqa: E402
from app.models.footfall import FootfallLog  # noqa: E402


# ─── Default day-of-week multipliers ─────────────────────────────────────────
# Index 0 = Monday, 6 = Sunday.  These encode the typical PHC/CHC traffic
# pattern observed in India (HMIS / NHM literature).
_DEFAULT_DOW_MULTIPLIERS: dict[str, list[float]] = {
    "PHC":               [0.80, 1.00, 1.05, 1.05, 1.00, 0.70, 0.40],
    "CHC":               [0.85, 1.00, 1.05, 1.05, 1.00, 0.75, 0.50],
    "tertiary_referral": [0.90, 1.00, 1.02, 1.02, 1.00, 0.85, 0.70],
}

# Metric name that carries the patient-count signal in daily_averages
_FOOTFALL_METRIC = "outpatient_visits"


# ─── Helper utilities ─────────────────────────────────────────────────────────

def _build_engine(database_url: str):
    """Return a synchronous SQLAlchemy engine, trying port 5432 then 5433."""
    sync_url = re.sub(r"^postgresql\+asyncpg", "postgresql+psycopg2", database_url)
    candidates = [sync_url, re.sub(r":5432/", ":5433/", sync_url)]

    for url in candidates:
        masked = re.sub(r":[^/@:]+@", ":***@", url)
        try:
            logger.info("Connecting to DB: %s", masked)
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            with engine.connect():
                pass  # validate
            logger.info("Connected successfully.")
            return engine
        except Exception as exc:
            logger.warning("Could not connect to %s — %s", masked, exc)

    return None


def _get_footfall_average(
    session: Session, facility_id: object
) -> Optional[DailyAverage]:
    """Return the outpatient_visits DailyAverage row for a facility, or None."""
    return (
        session.query(DailyAverage)
        .filter(
            DailyAverage.facility_id == facility_id,
            DailyAverage.metric_name == _FOOTFALL_METRIC,
        )
        .order_by(DailyAverage.recorded_at.desc())
        .first()
    )


def _has_any_daily_average(session: Session, facility_id: object) -> bool:
    """Return True if the facility has at least one daily_averages row."""
    return (
        session.query(DailyAverage)
        .filter(DailyAverage.facility_id == facility_id)
        .limit(1)
        .count()
        > 0
    )


def _dow_multiplier(
    facility_type: FacilityType,
    weekday: int,
    multipliers: dict[str, list[float]],
) -> float:
    """Return the day-of-week scaling factor for the given facility type."""
    key = facility_type.value  # e.g. "PHC", "CHC", "tertiary_referral"
    row = multipliers.get(key, multipliers.get("CHC", [1.0] * 7))
    return row[weekday % 7]


def _sample_patient_count(lam: float, rng: np.random.Generator) -> int:
    """Draw a non-negative integer from Poisson(λ).

    If λ ≤ 0 (degenerate data), return 0 rather than crash.
    """
    if lam <= 0:
        return 0
    return int(rng.poisson(lam=lam))


# ─── Core generation logic ────────────────────────────────────────────────────

def generate_footfall_logs(
    session: Session,
    facilities: list[Facility],
    n_days: int,
    start_date: date,
    dow_multipliers: dict[str, list[float]],
    rng: np.random.Generator,
    dry_run: bool,
) -> dict[str, int]:
    """Generate and optionally persist footfall log rows.

    Returns a summary dict: {facility_id: rows_written}.

    Invariants enforced here:
    - Skip facilities with zero daily_averages rows (warn, never invent).
    - Skip facilities whose outpatient_visits average is missing (warn).
    - Every row: is_simulated=True, basis="real_average:<source_url>".
    """
    summary: dict[str, int] = {}

    for facility in facilities:
        fac_label = f"'{facility.name}' ({facility.facility_id})"

        # ── Guard 1: facility must have ANY daily_averages row ────────────────
        if not _has_any_daily_average(session, facility.id):
            logger.warning(
                "SKIP %s — no rows in daily_averages. "
                "Load real data first (load_facility.py) before generating logs.",
                fac_label,
            )
            summary[facility.facility_id] = 0
            continue

        # ── Guard 2: we specifically need the outpatient_visits average ───────
        da = _get_footfall_average(session, facility.id)
        if da is None:
            logger.warning(
                "SKIP %s — daily_averages exists but has no '%s' metric. "
                "Cannot generate footfall without a real anchor value.",
                fac_label,
                _FOOTFALL_METRIC,
            )
            summary[facility.facility_id] = 0
            continue

        avg_value = float(da.avg_value)
        source_url = da.source_url
        basis = f"real_average:{source_url}"

        logger.info(
            "Generating %d days for %s | λ=%.2f | metric=%s | source=%s",
            n_days,
            fac_label,
            avg_value,
            _FOOTFALL_METRIC,
            source_url,
        )

        rows_written = 0
        for day_offset in range(n_days):
            day = start_date + timedelta(days=day_offset)
            weekday = day.weekday()  # 0=Mon … 6=Sun

            # Scale λ by the day-of-week multiplier for this facility type
            multiplier = _dow_multiplier(
                facility.facility_type, weekday, dow_multipliers
            )
            lam = avg_value * multiplier

            patient_count = _sample_patient_count(lam, rng)

            log = FootfallLog(
                facility_id=facility.id,
                date=day,
                patient_count=patient_count,
                department=None,  # whole-facility count
                is_simulated=True,
                basis=basis,
            )

            if not dry_run:
                session.add(log)

            rows_written += 1

        if not dry_run:
            session.flush()  # batch per facility, commit once at the end

        summary[facility.facility_id] = rows_written
        logger.info(
            "  → %d rows %s for %s",
            rows_written,
            "(dry-run, not committed)" if dry_run else "queued",
            fac_label,
        )

    return summary


# ─── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate simulated daily footfall logs grounded in real daily_averages. "
            "Facilities without any daily_averages rows are SKIPPED entirely."
        )
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of logs to generate (default: 90)",
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=None,
        help=(
            "ISO start date for the generated window (default: today - N days). "
            "Example: 2024-01-01"
        ),
    )
    parser.add_argument(
        "--facility-id",
        type=str,
        default=None,
        metavar="FAC_ID",
        help=(
            "Restrict generation to a single facility by its human-readable "
            "facility_id (e.g. MH-PHC-0042). Defaults to all facilities."
        ),
    )
    parser.add_argument(
        "--dow-config",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Path to a JSON file overriding day-of-week multipliers per "
            "facility_type. See module docstring for format."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Integer seed for the random number generator (for reproducibility).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without committing to the database.",
    )
    args = parser.parse_args()

    # ── Resolve start date ────────────────────────────────────────────────────
    start_date: date = args.start_date or (date.today() - timedelta(days=args.days))

    # ── Load day-of-week multipliers ──────────────────────────────────────────
    dow_multipliers = dict(_DEFAULT_DOW_MULTIPLIERS)
    if args.dow_config:
        config_path = Path(args.dow_config)
        if not config_path.exists():
            logger.error("--dow-config file not found: %s", config_path)
            sys.exit(1)
        with config_path.open() as fh:
            overrides: dict = json.load(fh)
        # Validate structure minimally
        for ftype, mults in overrides.items():
            if not isinstance(mults, list) or len(mults) != 7:
                logger.error(
                    "Invalid dow-config: '%s' must have exactly 7 float values.", ftype
                )
                sys.exit(1)
            if not all(isinstance(m, (int, float)) for m in mults):
                logger.error(
                    "Invalid dow-config: all values for '%s' must be numeric.", ftype
                )
                sys.exit(1)
        dow_multipliers.update(overrides)
        logger.info("Loaded day-of-week overrides from %s", args.dow_config)

    # ── Database connection ───────────────────────────────────────────────────
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set.")
        sys.exit(1)

    engine = _build_engine(database_url)
    if engine is None:
        logger.error(
            "Could not connect to the database. "
            "Ensure the Postgres container is running."
        )
        sys.exit(1)

    SessionFactory = sessionmaker(bind=engine)
    session: Session = SessionFactory()

    # ── Resolve facilities ────────────────────────────────────────────────────
    try:
        query = session.query(Facility)
        if args.facility_id:
            query = query.filter(Facility.facility_id == args.facility_id)
        facilities: list[Facility] = query.all()
    except Exception as exc:
        logger.error("Failed to query facilities: %s", exc)
        session.close()
        sys.exit(1)

    if not facilities:
        if args.facility_id:
            logger.error(
                "No facility found with facility_id='%s'. "
                "Run load_facility.py first.",
                args.facility_id,
            )
        else:
            logger.warning(
                "No facilities found in the database. "
                "Run load_facility.py to seed facility data first."
            )
        session.close()
        sys.exit(0)

    logger.info(
        "Found %d facilit%s. Generating %d days of logs starting %s.%s",
        len(facilities),
        "y" if len(facilities) == 1 else "ies",
        args.days,
        start_date.isoformat(),
        " [DRY RUN — no DB writes]" if args.dry_run else "",
    )

    # ── Generate ──────────────────────────────────────────────────────────────
    rng = np.random.default_rng(args.seed)

    try:
        summary = generate_footfall_logs(
            session=session,
            facilities=facilities,
            n_days=args.days,
            start_date=start_date,
            dow_multipliers=dow_multipliers,
            rng=rng,
            dry_run=args.dry_run,
        )

        if not args.dry_run:
            session.commit()
            logger.info("Transaction committed.")
        else:
            session.rollback()
            logger.info("Dry-run complete — no changes written.")

    except Exception as exc:
        session.rollback()
        logger.error("Transaction rolled back due to error: %s", exc)
        raise
    finally:
        session.close()

    # ── Final summary ─────────────────────────────────────────────────────────
    total_rows = sum(summary.values())
    skipped = sum(1 for v in summary.values() if v == 0)
    written = len(summary) - skipped

    logger.info(
        "Done. Facilities processed: %d | skipped (no daily_averages): %d | "
        "rows %s: %d",
        len(summary),
        skipped,
        "would write" if args.dry_run else "written",
        total_rows,
    )

    if skipped:
        skipped_ids = [fid for fid, count in summary.items() if count == 0]
        logger.warning(
            "Skipped facilities (no real data — load_facility.py required): %s",
            ", ".join(skipped_ids),
        )


if __name__ == "__main__":
    main()
