from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from industrial_copilot.config import DASHBOARD_PATH, DB_PATH, OUTPUT_DIR, RAW_DIR
from industrial_copilot.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.outputs = run_pipeline(regenerate_data=True)
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls) -> None:
        cls.conn.close()

    def count_rows(self, table_name: str) -> int:
        return self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    def test_pipeline_outputs_exist(self) -> None:
        self.assertTrue(DB_PATH.exists())
        self.assertTrue(DASHBOARD_PATH.exists())
        self.assertTrue((OUTPUT_DIR / "case_summary.md").exists())
        self.assertTrue((OUTPUT_DIR / "dashboard_preview.svg").exists())
        self.assertTrue((RAW_DIR / "sensor_readings.csv").exists())

    def test_bronze_silver_gold_tables_are_populated(self) -> None:
        self.assertGreater(self.count_rows("bronze_sensor_readings"), 1000)
        self.assertGreater(self.count_rows("silver_sensor_readings"), 1000)
        self.assertEqual(self.count_rows("gold_equipment_health_summary"), 4)
        self.assertGreaterEqual(self.count_rows("gold_work_order_copilot_briefs"), 3)

    def test_data_quality_layer_catches_intentional_dirty_records(self) -> None:
        issues = {
            row["issue_type"]: row["issue_count"]
            for row in self.conn.execute(
                """
                SELECT issue_type, COUNT(*) AS issue_count
                FROM data_quality_issues
                GROUP BY issue_type
                """
            )
        }
        self.assertGreaterEqual(issues.get("sensor_quality", 0), 3)
        self.assertGreaterEqual(issues.get("work_order_quality", 0), 1)

    def test_high_risk_equipment_is_prioritized(self) -> None:
        top = self.conn.execute(
            """
            SELECT equipment_id, risk_score, risk_tier
            FROM gold_equipment_health_summary
            ORDER BY risk_score DESC
            LIMIT 1
            """
        ).fetchone()
        self.assertIn(top["equipment_id"], {"PUMP-101", "COMP-201", "GEN-401"})
        self.assertIn(top["risk_tier"], {"critical", "watch"})


if __name__ == "__main__":
    unittest.main()
