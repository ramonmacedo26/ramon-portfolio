from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from document_ai_ops.config import (
    ARCHITECTURE_FLOW_PATH,
    DASHBOARD_PATH,
    DB_PATH,
    EXCEPTIONS_CSV_PATH,
    MASTER_CSV_PATH,
    MASTER_XLSX_PATH,
    VALIDATION_CSV_PATH,
)
from document_ai_ops.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        run_pipeline(regenerate_data=True)
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
        self.assertTrue(MASTER_CSV_PATH.exists())
        self.assertTrue(MASTER_XLSX_PATH.exists())
        self.assertTrue(EXCEPTIONS_CSV_PATH.exists())
        self.assertTrue(VALIDATION_CSV_PATH.exists())

    def test_tables_are_populated(self) -> None:
        self.assertGreaterEqual(self.count_rows("bronze_documents"), 20)
        self.assertGreaterEqual(self.count_rows("silver_document_records"), 20)
        self.assertGreaterEqual(self.count_rows("validation_issues"), 4)

    def test_expected_bad_records_are_caught(self) -> None:
        issues = {
            row["issue_type"]: row["issue_count"]
            for row in self.conn.execute(
                "SELECT issue_type, COUNT(*) AS issue_count FROM validation_issues GROUP BY issue_type"
            )
        }
        self.assertGreaterEqual(issues.get("missing_required_field", 0), 1)
        self.assertGreaterEqual(issues.get("invalid_priority", 0), 1)
        self.assertGreaterEqual(issues.get("negative_value", 0), 1)


if __name__ == "__main__":
    unittest.main()
