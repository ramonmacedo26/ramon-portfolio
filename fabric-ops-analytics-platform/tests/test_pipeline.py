from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fabric_ops_platform.config import ARCHITECTURE_FLOW_PATH, DASHBOARD_PATH, DB_PATH, OUTPUT_DIR, RAW_DIR
from fabric_ops_platform.pipeline import run_pipeline


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

    def test_outputs_exist(self) -> None:
        self.assertTrue(DB_PATH.exists())
        self.assertTrue(DASHBOARD_PATH.exists())
        self.assertTrue(ARCHITECTURE_FLOW_PATH.exists())
        self.assertTrue((OUTPUT_DIR / "case_summary.md").exists())
        self.assertTrue((RAW_DIR / "service_tickets.csv").exists())

    def test_tables_are_populated(self) -> None:
        self.assertGreater(self.count_rows("silver_service_tickets"), 300)
        self.assertGreater(self.count_rows("silver_technician_shifts"), 150)
        self.assertEqual(self.count_rows("gold_site_operations_summary"), 4)
        self.assertEqual(self.count_rows("gold_technician_capacity_summary"), 8)

    def test_quality_layer_catches_intentional_bad_records(self) -> None:
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
        self.assertGreaterEqual(issues.get("ticket_quality", 0), 1)
        self.assertGreaterEqual(issues.get("shift_quality", 0), 1)
        self.assertGreaterEqual(issues.get("downtime_quality", 0), 1)
        self.assertGreaterEqual(issues.get("cost_quality", 0), 1)

    def test_exec_kpis_are_present(self) -> None:
        metrics = {
            row["metric_name"]: row["metric_value"]
            for row in self.conn.execute("SELECT metric_name, metric_value FROM gold_exec_kpis")
        }
        self.assertIn("open_backlog", metrics)
        self.assertIn("sla_breaches", metrics)
        self.assertGreater(metrics["open_backlog"], 0)


if __name__ == "__main__":
    unittest.main()
