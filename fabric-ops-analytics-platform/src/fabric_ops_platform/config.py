from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DB_PATH = WAREHOUSE_DIR / "fabric_ops.db"
DASHBOARD_PATH = OUTPUT_DIR / "dashboard.html"
ARCHITECTURE_FLOW_PATH = OUTPUT_DIR / "architecture_flow.svg"

SITES = {
    "RIO": {"name": "Rio Service Hub", "region": "Brazil Southeast"},
    "MCZ": {"name": "Macae Offshore Support", "region": "Brazil Southeast"},
    "VIX": {"name": "Vitoria Operations Base", "region": "Brazil Southeast"},
    "SSA": {"name": "Salvador Reliability Center", "region": "Brazil Northeast"},
}

TECHNICIANS = {
    "T-101": {"name": "Ana Costa", "site_id": "RIO", "specialty": "electrical"},
    "T-102": {"name": "Bruno Lima", "site_id": "RIO", "specialty": "mechanical"},
    "T-201": {"name": "Carlos Dias", "site_id": "MCZ", "specialty": "rotating"},
    "T-202": {"name": "Daniela Rocha", "site_id": "MCZ", "specialty": "inspection"},
    "T-301": {"name": "Erica Souza", "site_id": "VIX", "specialty": "instrumentation"},
    "T-302": {"name": "Felipe Melo", "site_id": "VIX", "specialty": "mechanical"},
    "T-401": {"name": "Gabriela Reis", "site_id": "SSA", "specialty": "reliability"},
    "T-402": {"name": "Hugo Nunes", "site_id": "SSA", "specialty": "electrical"},
}

ALLOWED_TICKET_STATUS = {"open", "in_progress", "resolved"}
ALLOWED_PRIORITY = {"critical", "high", "medium", "low"}
