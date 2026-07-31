from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta

from .config import EQUIPMENT, RAW_DIR


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_sensor_rows(seed: int = 42) -> list[dict[str, str]]:
    random.seed(seed)
    start = datetime(2026, 7, 1, 0, 0, 0)
    rows: list[dict[str, str]] = []

    for equipment_id in EQUIPMENT:
        for hour in range(14 * 24):
            ts = start + timedelta(hours=hour)
            day_wave = math.sin(hour / 24 * math.pi * 2)
            base_temp = 58 + 7 * day_wave + random.uniform(-2.0, 2.0)
            base_vibration = 3.2 + random.uniform(-0.4, 0.5)
            base_pressure = 8.0 + random.uniform(-0.8, 0.8)
            base_energy = 118 + 14 * max(day_wave, 0) + random.uniform(-5, 5)

            if equipment_id == "PUMP-101" and 8 * 24 <= hour <= 9 * 24 + 8:
                base_vibration += 5.3
                base_temp += 13
                base_energy += 38
            if equipment_id == "COMP-201" and 10 * 24 <= hour <= 10 * 24 + 14:
                base_pressure += 5.5
                base_temp += 10
            if equipment_id == "GEN-401" and 12 * 24 <= hour <= 12 * 24 + 6:
                base_energy += 82

            row = {
                "event_ts": ts.isoformat(timespec="minutes"),
                "equipment_id": equipment_id,
                "temperature_c": f"{base_temp:.2f}",
                "vibration_mm_s": f"{base_vibration:.2f}",
                "pressure_bar": f"{base_pressure:.2f}",
                "energy_kwh": f"{base_energy:.2f}",
            }
            rows.append(row)

    # Intentional dirty records for the quality layer to catch.
    rows.append(rows[25].copy())  # duplicate equipment/timestamp
    dirty = rows[140].copy()
    dirty["temperature_c"] = ""
    rows.append(dirty)
    bad_pressure = rows[412].copy()
    bad_pressure["pressure_bar"] = "999.00"
    rows.append(bad_pressure)
    return rows


def generate_work_orders() -> list[dict[str, str]]:
    return [
        {
            "work_order_id": "WO-1001",
            "equipment_id": "PUMP-101",
            "opened_at": "2026-07-09T08:30",
            "closed_at": "",
            "priority": "critical",
            "status": "open",
            "description": "High vibration reported near pump bearing housing.",
        },
        {
            "work_order_id": "WO-1002",
            "equipment_id": "COMP-201",
            "opened_at": "2026-07-11T06:45",
            "closed_at": "",
            "priority": "high",
            "status": "in_progress",
            "description": "Pressure spike and abnormal outlet temperature.",
        },
        {
            "work_order_id": "WO-1003",
            "equipment_id": "HX-301",
            "opened_at": "2026-07-05T13:10",
            "closed_at": "2026-07-06T16:20",
            "priority": "medium",
            "status": "closed",
            "description": "Routine fouling inspection and cleaning.",
        },
        {
            "work_order_id": "WO-1004",
            "equipment_id": "GEN-401",
            "opened_at": "2026-07-13T09:05",
            "closed_at": "",
            "priority": "high",
            "status": "open",
            "description": "Unexpected energy draw during backup readiness test.",
        },
        {
            "work_order_id": "WO-1005",
            "equipment_id": "PUMP-101",
            "opened_at": "2026-07-02T10:00",
            "closed_at": "2026-07-02T14:30",
            "priority": "low",
            "status": "closed",
            "description": "Lubrication check completed.",
        },
        {
            "work_order_id": "WO-1006",
            "equipment_id": "COMP-201",
            "opened_at": "2026-07-14T09:00",
            "closed_at": "",
            "priority": "high",
            "status": "waiting_vendor",
            "description": "Vendor follow-up needed for pressure valve replacement.",
        },
    ]


def generate_cost_events() -> list[dict[str, str]]:
    return [
        {"cost_id": "C-001", "event_date": "2026-07-02", "equipment_id": "PUMP-101", "category": "labor", "amount_usd": "320.00"},
        {"cost_id": "C-002", "event_date": "2026-07-05", "equipment_id": "HX-301", "category": "parts", "amount_usd": "890.00"},
        {"cost_id": "C-003", "event_date": "2026-07-09", "equipment_id": "PUMP-101", "category": "parts", "amount_usd": "2750.00"},
        {"cost_id": "C-004", "event_date": "2026-07-10", "equipment_id": "PUMP-101", "category": "downtime", "amount_usd": "4800.00"},
        {"cost_id": "C-005", "event_date": "2026-07-11", "equipment_id": "COMP-201", "category": "labor", "amount_usd": "1550.00"},
        {"cost_id": "C-006", "event_date": "2026-07-13", "equipment_id": "GEN-401", "category": "fuel", "amount_usd": "1280.00"},
        {"cost_id": "C-007", "event_date": "2026-07-14", "equipment_id": "COMP-201", "category": "parts", "amount_usd": "3600.00"},
    ]


def generate_work_reports() -> list[dict[str, str]]:
    return [
        {
            "document_id": "DOC-001",
            "document_date": "2026-07-09",
            "equipment_id": "PUMP-101",
            "author": "Maintenance Supervisor",
            "report_text": "Inspection found high vibration, bearing noise, and oil residue near the pump seal. Recommend urgent alignment check.",
        },
        {
            "document_id": "DOC-002",
            "document_date": "2026-07-11",
            "equipment_id": "COMP-201",
            "author": "Field Engineer",
            "report_text": "Compressor showed pressure instability, elevated outlet temperature, and possible valve restriction during startup.",
        },
        {
            "document_id": "DOC-003",
            "document_date": "2026-07-06",
            "equipment_id": "HX-301",
            "author": "Reliability Analyst",
            "report_text": "Heat exchanger cleaning completed. No leak detected. Monitor fouling trend in the next cycle.",
        },
        {
            "document_id": "DOC-004",
            "document_date": "2026-07-13",
            "equipment_id": "GEN-401",
            "author": "Operations Lead",
            "report_text": "Generator readiness test caused abnormal energy consumption. Battery bank and load transfer behavior should be reviewed.",
        },
    ]


def generate_all() -> None:
    write_csv(
        RAW_DIR / "sensor_readings.csv",
        ["event_ts", "equipment_id", "temperature_c", "vibration_mm_s", "pressure_bar", "energy_kwh"],
        generate_sensor_rows(),
    )
    write_csv(
        RAW_DIR / "maintenance_orders.csv",
        ["work_order_id", "equipment_id", "opened_at", "closed_at", "priority", "status", "description"],
        generate_work_orders(),
    )
    write_csv(
        RAW_DIR / "cost_events.csv",
        ["cost_id", "event_date", "equipment_id", "category", "amount_usd"],
        generate_cost_events(),
    )
    write_csv(
        RAW_DIR / "work_reports.csv",
        ["document_id", "document_date", "equipment_id", "author", "report_text"],
        generate_work_reports(),
    )


if __name__ == "__main__":
    generate_all()
    print(f"Generated synthetic raw data in {RAW_DIR}")
