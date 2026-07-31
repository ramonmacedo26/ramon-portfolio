from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
INBOX_DIR = DATA_DIR / "inbox"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DOCS_DIR = PROJECT_ROOT / "docs"

DB_PATH = WAREHOUSE_DIR / "document_ai_ops.db"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"
ARCHITECTURE_FLOW_PATH = OUTPUT_DIR / "architecture_flow.svg"
MASTER_CSV_PATH = OUTPUT_DIR / "master_operational_intake.csv"
MASTER_XLSX_PATH = OUTPUT_DIR / "master_operational_intake.xlsx"
EXCEPTIONS_CSV_PATH = OUTPUT_DIR / "exceptions_queue.csv"
EXCEPTIONS_XLSX_PATH = OUTPUT_DIR / "exceptions_queue.xlsx"
VALIDATION_CSV_PATH = OUTPUT_DIR / "validation_results.csv"
CASE_SUMMARY_PATH = OUTPUT_DIR / "case_summary.md"

DOCUMENT_TYPES = {
    "work_orders": "maintenance_work_order",
    "technician_reports": "technician_service_report",
    "inspection_checklists": "inspection_checklist",
    "vendor_requests": "vendor_service_request",
    "parts_requests": "spare_parts_request",
}

PRIORITY_ORDER = {"critical", "high", "medium", "low"}
STATUS_ORDER = {"open", "in_progress", "pending_vendor", "approved", "completed", "closed"}
SITES = {"RIO", "MCZ", "VIX", "SSA"}

ROUTE_BY_CATEGORY = {
    "electrical": "electrical_team",
    "mechanical": "mechanical_team",
    "inspection": "inspection_team",
    "instrumentation": "instrumentation_team",
    "procurement": "supply_chain",
    "vendor_support": "vendor_management",
}
