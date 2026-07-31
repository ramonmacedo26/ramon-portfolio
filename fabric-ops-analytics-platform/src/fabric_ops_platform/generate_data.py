from __future__ import annotations

import csv
import random
from datetime import date, timedelta

from .config import RAW_DIR, SITES, TECHNICIANS


def daterange(start: date, days: int) -> list[date]:
    return [start + timedelta(days=offset) for offset in range(days)]


def write_csv(path, fieldnames, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_service_tickets(seed: int = 26) -> None:
    random.seed(seed)
    rows = []
    priorities = ["critical", "high", "medium", "low"]
    statuses = ["open", "in_progress", "resolved"]
    categories = ["electrical", "mechanical", "instrumentation", "inspection"]
    opened_dates = daterange(date(2026, 6, 15), 35)
    counter = 1000
    for site_id in SITES:
        for opened_at in opened_dates:
            for _ in range(random.randint(2, 5)):
                priority = random.choices(priorities, weights=[1, 2, 3, 2])[0]
                status = random.choices(statuses, weights=[3, 2, 4])[0]
                sla_hours = {"critical": 8, "high": 24, "medium": 72, "low": 120}[priority]
                resolution_hours = max(2, int(random.gauss(sla_hours * 0.9, sla_hours * 0.5)))
                if status != "resolved":
                    resolution_hours = ""
                rows.append(
                    {
                        "ticket_id": f"INC-{counter}",
                        "site_id": site_id,
                        "opened_date": opened_at.isoformat(),
                        "priority": priority,
                        "status": status,
                        "category": random.choice(categories),
                        "estimated_sla_hours": sla_hours,
                        "resolution_hours": resolution_hours,
                    }
                )
                counter += 1

    rows.append(
        {
            "ticket_id": "INC-9999",
            "site_id": "UNK",
            "opened_date": "2026-07-05",
            "priority": "urgent",
            "status": "open",
            "category": "mechanical",
            "estimated_sla_hours": 4,
            "resolution_hours": "",
        }
    )
    write_csv(
        RAW_DIR / "service_tickets.csv",
        [
            "ticket_id",
            "site_id",
            "opened_date",
            "priority",
            "status",
            "category",
            "estimated_sla_hours",
            "resolution_hours",
        ],
        rows,
    )


def generate_technician_shifts(seed: int = 42) -> None:
    random.seed(seed)
    rows = []
    shift_dates = daterange(date(2026, 7, 1), 21)
    for technician_id, meta in TECHNICIANS.items():
        for shift_date in shift_dates:
            scheduled = 8
            productive = max(2.5, round(random.gauss(6.4, 1.0), 1))
            overtime = max(0.0, round(random.gauss(0.8 if meta["site_id"] == "MCZ" else 0.3, 0.6), 1))
            rows.append(
                {
                    "technician_id": technician_id,
                    "site_id": meta["site_id"],
                    "shift_date": shift_date.isoformat(),
                    "scheduled_hours": scheduled,
                    "productive_hours": productive,
                    "overtime_hours": overtime,
                }
            )
    rows.append(
        {
            "technician_id": "T-404",
            "site_id": "SSA",
            "shift_date": "2026-07-06",
            "scheduled_hours": 8,
            "productive_hours": 12.5,
            "overtime_hours": 5.0,
        }
    )
    write_csv(
        RAW_DIR / "technician_shifts.csv",
        [
            "technician_id",
            "site_id",
            "shift_date",
            "scheduled_hours",
            "productive_hours",
            "overtime_hours",
        ],
        rows,
    )


def generate_downtime_events(seed: int = 7) -> None:
    random.seed(seed)
    rows = []
    causes = ["parts delay", "crew unavailability", "repeat failure", "inspection wait", "vendor dependency"]
    dates = daterange(date(2026, 7, 1), 21)
    counter = 500
    for site_id in SITES:
        for event_date in dates:
            if random.random() < 0.55:
                rows.append(
                    {
                        "event_id": f"DT-{counter}",
                        "site_id": site_id,
                        "event_date": event_date.isoformat(),
                        "downtime_hours": round(random.uniform(0.8, 6.5), 1),
                        "cause_group": random.choice(causes),
                    }
                )
                counter += 1
    rows.append(
        {
            "event_id": "DT-999",
            "site_id": "RIO",
            "event_date": "2026-07-03",
            "downtime_hours": -2.0,
            "cause_group": "parts delay",
        }
    )
    write_csv(
        RAW_DIR / "downtime_events.csv",
        ["event_id", "site_id", "event_date", "downtime_hours", "cause_group"],
        rows,
    )


def generate_cost_ledger(seed: int = 11) -> None:
    random.seed(seed)
    rows = []
    cost_types = ["labor", "vendor", "parts", "travel"]
    dates = daterange(date(2026, 7, 1), 21)
    counter = 800
    for site_id in SITES:
        for event_date in dates:
            rows.append(
                {
                    "cost_id": f"C-{counter}",
                    "site_id": site_id,
                    "event_date": event_date.isoformat(),
                    "cost_type": random.choice(cost_types),
                    "amount_usd": round(random.uniform(220, 1850), 2),
                }
            )
            counter += 1
    rows.append(
        {
            "cost_id": "C-999",
            "site_id": "MCZ",
            "event_date": "2026-07-08",
            "cost_type": "vendor",
            "amount_usd": -120.0,
        }
    )
    write_csv(
        RAW_DIR / "cost_ledger.csv",
        ["cost_id", "site_id", "event_date", "cost_type", "amount_usd"],
        rows,
    )


def generate_all() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    generate_service_tickets()
    generate_technician_shifts()
    generate_downtime_events()
    generate_cost_ledger()

