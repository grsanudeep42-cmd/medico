"""
test_metrics.py — Unit tests for facility risk assessment and audit calculations.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

# Bootstrap sys.path to find modules
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai.audit_tests import calculate_facility_gap
from ai.flag_facilities import (
    calculate_bed_volatility,
    calculate_doctor_attendance,
    calculate_stockout_frequency,
)
from app.config import settings
from app.models.bed import Bed
from app.models.facility import Facility
from app.models.inventory import StockLevel
from app.models.staff import AttendanceLog, Staff


class TestAuditAndFlaggingMetrics(unittest.TestCase):
    def setUp(self):
        # Configure a standard set of required tests in config for predictability
        settings.required_tests_by_tier["primary"] = [
            "Hb",
            "urine routine",
            "blood sugar",
            "malaria smear",
        ]
        settings.required_tests_by_tier["community"] = [
            "Hb",
            "urine routine",
            "blood sugar",
            "malaria smear",
            "X-ray",
            "ECG",
            "wider pathology panel",
        ]

    def test_calculate_facility_gap_full_compliance(self):
        # 100% compliant: all required tests available
        facility = MagicMock(spec=Facility)
        facility.tier.value = "primary"
        available = {"Hb", "urine routine", "blood sugar", "malaria smear"}
        missing, gap_pct = calculate_facility_gap(facility, available)
        self.assertEqual(missing, [])
        self.assertEqual(gap_pct, 0.0)

    def test_calculate_facility_gap_partial_compliance(self):
        # 50% compliant: 2 out of 4 missing
        facility = MagicMock(spec=Facility)
        facility.tier.value = "primary"
        available = {"Hb", "urine routine"}
        missing, gap_pct = calculate_facility_gap(facility, available)
        self.assertEqual(set(missing), {"blood sugar", "malaria smear"})
        self.assertEqual(gap_pct, 50.0)

    def test_calculate_facility_gap_empty_required(self):
        # Facility tier not found or no tests required
        facility = MagicMock(spec=Facility)
        facility.tier.value = "unknown_tier"
        available = {"Hb"}
        missing, gap_pct = calculate_facility_gap(facility, available)
        self.assertEqual(missing, [])
        self.assertEqual(gap_pct, 0.0)

    def test_calculate_stockout_frequency_no_levels(self):
        # No stock levels recorded -> 0.0
        session = MagicMock()
        session.query().filter().all.return_value = []
        freq = calculate_stockout_frequency(session, "dummy-id")
        self.assertEqual(freq, 0.0)

    def test_calculate_stockout_frequency_calculation(self):
        # 2 out of 4 items stocked out -> 50.0%
        session = MagicMock()
        lvl1 = MagicMock(spec=StockLevel, quantity=0.0)
        lvl2 = MagicMock(spec=StockLevel, quantity=10.0)
        lvl3 = MagicMock(spec=StockLevel, quantity=-2.5)  # negative counts as stocked out
        lvl4 = MagicMock(spec=StockLevel, quantity=5.0)
        session.query().filter().all.return_value = [lvl1, lvl2, lvl3, lvl4]

        freq = calculate_stockout_frequency(session, "dummy-id")
        self.assertEqual(freq, 50.0)

    def test_calculate_bed_volatility_insufficient_data(self):
        # Fewer than 2 snapshots -> volatility 0.0
        session = MagicMock()
        session.query().filter().order_by().all.return_value = [MagicMock(spec=Bed)]
        vol = calculate_bed_volatility(session, "dummy-id")
        self.assertEqual(vol, 0.0)

    def test_calculate_bed_volatility_calculation(self):
        # Calculate standard deviation of [0.5, 0.5, 0.5] -> 0.0 (no variance)
        # Calculate standard deviation of [1.0, 0.0] -> 0.5
        session = MagicMock()
        
        bed1 = MagicMock(spec=Bed, total_beds=10, occupied_beds=10) # 1.0 occupancy
        bed2 = MagicMock(spec=Bed, total_beds=10, occupied_beds=0)  # 0.0 occupancy
        
        session.query().filter().order_by().all.return_value = [bed1, bed2]
        vol = calculate_bed_volatility(session, "dummy-id")
        self.assertAlmostEqual(vol, 0.5)

    def test_calculate_doctor_attendance_no_doctors(self):
        # No doctors -> 100.0%
        session = MagicMock()
        session.query().filter().all.return_value = []
        att = calculate_doctor_attendance(session, "dummy-id")
        self.assertEqual(att, 100.0)

    def test_calculate_doctor_attendance_calculation(self):
        # 1 doctor present 8 out of 10 days -> 80.0%
        session = MagicMock()
        
        doc1 = MagicMock(spec=Staff, id="doc-1")
        
        logs = []
        for i in range(8):
            logs.append(MagicMock(spec=AttendanceLog, present=True))
        for i in range(2):
            logs.append(MagicMock(spec=AttendanceLog, present=False))

        # First query fetches doctors, second fetches logs
        session.query.return_value.filter.return_value.all.side_effect = [[doc1], logs]

        att = calculate_doctor_attendance(session, "dummy-id")
        self.assertEqual(att, 80.0)


if __name__ == "__main__":
    unittest.main()
