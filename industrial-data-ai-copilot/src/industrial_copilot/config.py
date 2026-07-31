from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DB_PATH = WAREHOUSE_DIR / "industrial_ops.db"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"

EQUIPMENT = {
    "PUMP-101": {"name": "Primary Transfer Pump", "site": "Macae", "criticality": "high"},
    "COMP-201": {"name": "Gas Compressor", "site": "Macae", "criticality": "high"},
    "HX-301": {"name": "Heat Exchanger", "site": "Rio", "criticality": "medium"},
    "GEN-401": {"name": "Backup Generator", "site": "Rio", "criticality": "medium"},
}

ALLOWED_WORK_ORDER_STATUS = {"open", "in_progress", "closed"}
ALLOWED_PRIORITY = {"low", "medium", "high", "critical"}

SENSOR_THRESHOLDS = {
    "temperature_c_max": 82.0,
    "vibration_mm_s_max": 7.5,
    "pressure_bar_min": 4.0,
    "pressure_bar_max": 12.0,
    "energy_kwh_max": 185.0,
}
