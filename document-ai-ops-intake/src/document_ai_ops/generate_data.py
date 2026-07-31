from __future__ import annotations

import csv
from pathlib import Path

from .config import INBOX_DIR


WORK_ORDERS = [
    {
        "document_id": "WO-1001",
        "asset_id": "PMP-210",
        "asset_name": "Booster Pump A",
        "site": "RIO",
        "request_date": "2026-07-02",
        "priority": "critical",
        "issue_category": "mechanical",
        "failure_description": "Abnormal vibration near coupling and oil leak around seal housing.",
        "recommended_action": "Inspect alignment, replace seal, and validate bearing condition.",
        "requester": "Mariana Costa",
        "estimated_cost": "7800",
        "downtime_hours": "6.5",
        "status": "open",
    },
    {
        "document_id": "WO-1002",
        "asset_id": "CMP-115",
        "asset_name": "Air Compressor 2",
        "site": "MCZ",
        "request_date": "2026-07-03",
        "priority": "high",
        "issue_category": "electrical",
        "failure_description": "Motor trip observed twice during peak load.",
        "recommended_action": "Check MCC panel, cable insulation, and overload settings.",
        "requester": "Felipe Ramos",
        "estimated_cost": "4300",
        "downtime_hours": "3.0",
        "status": "in_progress",
    },
    {
        "document_id": "WO-1003",
        "asset_id": "VLV-332",
        "asset_name": "Control Valve 7",
        "site": "SSA",
        "request_date": "2026-07-04",
        "priority": "medium",
        "issue_category": "instrumentation",
        "failure_description": "Position feedback inconsistent with local indicator.",
        "recommended_action": "Recalibrate positioner and inspect signal wiring.",
        "requester": "Ana Beatriz",
        "estimated_cost": "1600",
        "downtime_hours": "1.5",
        "status": "open",
    },
    {
        "document_id": "WO-1004",
        "asset_id": "",
        "asset_name": "Cooling Fan 4",
        "site": "VIX",
        "request_date": "2026-07-05",
        "priority": "high",
        "issue_category": "mechanical",
        "failure_description": "Excessive noise reported during startup.",
        "recommended_action": "Inspect blades and fastening points.",
        "requester": "Carlos Nunes",
        "estimated_cost": "1200",
        "downtime_hours": "2.0",
        "status": "open",
    },
    {
        "document_id": "WO-1005",
        "asset_id": "HTX-901",
        "asset_name": "Heat Exchanger C",
        "site": "RIO",
        "request_date": "2026-07-06",
        "priority": "urgent",
        "issue_category": "mechanical",
        "failure_description": "Thermal efficiency drop and suspected fouling.",
        "recommended_action": "Plan cleaning window and inspect pressure drop.",
        "requester": "Bruno Lima",
        "estimated_cost": "5100",
        "downtime_hours": "4.0",
        "status": "open",
    },
    {
        "document_id": "WO-1006",
        "asset_id": "PMP-455",
        "asset_name": "Transfer Pump B",
        "site": "RIO",
        "request_date": "2026-07-07",
        "priority": "low",
        "issue_category": "inspection",
        "failure_description": "Routine inspection created for small casing paint damage.",
        "recommended_action": "Schedule coating touch-up in next maintenance window.",
        "requester": "Luciana Alves",
        "estimated_cost": "350",
        "downtime_hours": "0.0",
        "status": "closed",
    },
    {
        "document_id": "WO-1007",
        "asset_id": "GEN-808",
        "asset_name": "Backup Generator 1",
        "site": "MCZ",
        "request_date": "2026-07-08",
        "priority": "critical",
        "issue_category": "electrical",
        "failure_description": "Battery bank failed startup readiness test.",
        "recommended_action": "Replace battery set and repeat startup test.",
        "requester": "Daniel Rocha",
        "estimated_cost": "-900",
        "downtime_hours": "5.0",
        "status": "open",
    },
    {
        "document_id": "WO-1008",
        "asset_id": "TK-120",
        "asset_name": "Storage Tank 12",
        "site": "SSA",
        "request_date": "2026-07-09",
        "priority": "medium",
        "issue_category": "inspection",
        "failure_description": "Level gauge verification requested before audit.",
        "recommended_action": "Perform inspection and record calibration evidence.",
        "requester": "Julio Moreira",
        "estimated_cost": "800",
        "downtime_hours": "1.0",
        "status": "approved",
    },
]

TECHNICIAN_REPORTS = [
    {
        "document_id": "TR-2001",
        "event_date": "2026-07-02",
        "asset_id": "PMP-210",
        "site": "RIO",
        "technician": "Andre Silva",
        "issue_category": "mechanical",
        "failure_description": "Observed strong vibration and seal leakage during inspection round.",
        "recommended_action": "Urgent alignment check and seal replacement.",
        "part_code": "SEAL-44",
        "part_name": "Mechanical Seal Kit",
        "quantity": "1",
        "downtime_hours": "5.5",
        "status": "open",
    },
    {
        "document_id": "TR-2002",
        "event_date": "2026-07-03",
        "asset_id": "CMP-115",
        "site": "MCZ",
        "technician": "Patricia Melo",
        "issue_category": "electrical",
        "failure_description": "Breaker reset required after overload alarm.",
        "recommended_action": "Inspect overload relay and insulation resistance.",
        "part_code": "RELAY-19",
        "part_name": "Overload Relay",
        "quantity": "2",
        "downtime_hours": "2.0",
        "status": "in_progress",
    },
    {
        "document_id": "TR-2003",
        "event_date": "2026-07-04",
        "asset_id": "VLV-332",
        "site": "SSA",
        "technician": "Raquel Tavares",
        "issue_category": "instrumentation",
        "failure_description": "Positioner calibration drift confirmed.",
        "recommended_action": "Recalibrate and check pneumatic supply.",
        "part_code": "",
        "part_name": "",
        "quantity": "",
        "downtime_hours": "1.0",
        "status": "completed",
    },
    {
        "document_id": "TR-2004",
        "event_date": "2026-07-05",
        "asset_id": "FAN-404",
        "site": "VIX",
        "technician": "Paulo Souza",
        "issue_category": "mechanical",
        "failure_description": "Noise originates from loosened blade assembly.",
        "recommended_action": "Tighten assembly and inspect for imbalance.",
        "part_code": "BOLT-11",
        "part_name": "Blade Fastening Kit",
        "quantity": "1",
        "downtime_hours": "1.5",
        "status": "open",
    },
    {
        "document_id": "TR-2005",
        "event_date": "2026-07-06",
        "asset_id": "HTX-901",
        "site": "RIO",
        "technician": "Andre Silva",
        "issue_category": "mechanical",
        "failure_description": "Delta pressure indicates possible fouling build-up.",
        "recommended_action": "Open cleaning work package and inspect tubes.",
        "part_code": "",
        "part_name": "",
        "quantity": "",
        "downtime_hours": "4.0",
        "status": "pending_vendor",
    },
    {
        "document_id": "TR-2006",
        "event_date": "2026-07-07",
        "asset_id": "GEN-808",
        "site": "MCZ",
        "technician": "Carla Mendes",
        "issue_category": "electrical",
        "failure_description": "Battery voltage below acceptable startup threshold.",
        "recommended_action": "Replace cells and perform load bank test.",
        "part_code": "BAT-88",
        "part_name": "Industrial Battery Module",
        "quantity": "4",
        "downtime_hours": "4.5",
        "status": "open",
    },
]

INSPECTION_ROWS = [
    ["document_id", "event_date", "asset_id", "site", "priority", "issue_category", "failure_description", "recommended_action", "status"],
    ["IN-3001", "2026-07-02", "PMP-210", "RIO", "high", "inspection", "Thermography found hot coupling area.", "Schedule vibration route and thermal follow-up.", "open"],
    ["IN-3002", "2026-07-03", "TK-120", "SSA", "low", "inspection", "No abnormality detected. Routine compliance check.", "Close checklist and archive evidence.", "closed"],
    ["IN-3003", "2026-07-04", "CMP-115", "MCZ", "medium", "inspection", "Air line moisture above expected range.", "Inspect dryer and drain schedule.", "open"],
    ["IN-3004", "2026-07-05", "VLV-332", "SSA", "medium", "instrumentation", "Signal fluctuation during travel test.", "Inspect cabling and calibration setup.", "open"],
    ["IN-3005", "2026-07-06", "", "VIX", "medium", "inspection", "Missing asset reference in checklist.", "Review document before intake approval.", "open"],
    ["IN-3006", "2026-07-07", "GEN-808", "MCZ", "high", "electrical", "Starter test failed due to voltage drop.", "Prioritize battery replacement.", "open"],
]

VENDOR_REQUESTS = [
    {
        "document_id": "VR-4001",
        "request_date": "2026-07-05",
        "event_date": "2026-07-08",
        "asset_id": "HTX-901",
        "site": "RIO",
        "priority": "high",
        "vendor_name": "ThermoServ",
        "issue_category": "vendor_support",
        "failure_description": "Requesting cleaning contractor mobilization for exchanger fouling.",
        "recommended_action": "Confirm availability and quote window.",
        "estimated_cost": "12500",
        "status": "pending_vendor",
    },
    {
        "document_id": "VR-4002",
        "request_date": "2026-07-06",
        "event_date": "2026-07-10",
        "asset_id": "GEN-808",
        "site": "MCZ",
        "priority": "critical",
        "vendor_name": "PowerCore",
        "issue_category": "vendor_support",
        "failure_description": "Need urgent delivery of startup battery modules.",
        "recommended_action": "Expedite vendor response and reserve test team.",
        "estimated_cost": "9400",
        "status": "open",
    },
    {
        "document_id": "VR-4003",
        "request_date": "2026-07-07",
        "event_date": "",
        "asset_id": "PMP-455",
        "site": "RIO",
        "priority": "medium",
        "vendor_name": "",
        "issue_category": "vendor_support",
        "failure_description": "Need quote for repainting and coating touch-up.",
        "recommended_action": "Request vendor and approval path.",
        "estimated_cost": "1800",
        "status": "approved",
    },
    {
        "document_id": "VR-4004",
        "request_date": "2026-07-08",
        "event_date": "2026-07-12",
        "asset_id": "CMP-115",
        "site": "MCZ",
        "priority": "high",
        "vendor_name": "ElectroWorks",
        "issue_category": "electrical",
        "failure_description": "Specialist support requested for MCC inspection.",
        "recommended_action": "Coordinate shutdown slot and access permit.",
        "estimated_cost": "6200",
        "status": "in_progress",
    },
]

PART_REQUESTS = [
    ["document_id", "request_date", "asset_id", "site", "priority", "requester", "part_code", "part_name", "quantity", "estimated_cost", "status"],
    ["PR-5001", "2026-07-05", "PMP-210", "RIO", "high", "Mariana Costa", "SEAL-44", "Mechanical Seal Kit", "1", "1200", "approved"],
    ["PR-5002", "2026-07-06", "CMP-115", "MCZ", "high", "Felipe Ramos", "RELAY-19", "Overload Relay", "2", "900", "approved"],
    ["PR-5003", "2026-07-07", "GEN-808", "MCZ", "critical", "Daniel Rocha", "BAT-88", "Industrial Battery Module", "4", "4800", "open"],
    ["PR-5004", "2026-07-08", "VLV-332", "SSA", "medium", "Ana Beatriz", "AIR-22", "Pneumatic Filter", "1", "220", "closed"],
    ["PR-5005", "2026-07-08", "FAN-404", "VIX", "medium", "Carlos Nunes", "BOLT-11", "Blade Fastening Kit", "-1", "150", "open"],
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def render_work_order(doc: dict[str, str]) -> str:
    return "\n".join(
        [
            f"Work Order: {doc['document_id']}",
            f"Asset ID: {doc['asset_id']}",
            f"Asset Name: {doc['asset_name']}",
            f"Site: {doc['site']}",
            f"Request Date: {doc['request_date']}",
            f"Priority: {doc['priority']}",
            f"Category: {doc['issue_category']}",
            f"Requester: {doc['requester']}",
            f"Failure Description: {doc['failure_description']}",
            f"Recommended Action: {doc['recommended_action']}",
            f"Estimated Cost: {doc['estimated_cost']}",
            f"Downtime Hours: {doc['downtime_hours']}",
            f"Status: {doc['status']}",
        ]
    )


def render_technician_report(doc: dict[str, str]) -> str:
    return "\n".join(
        [
            f"# Technician Report {doc['document_id']}",
            f"- Event Date: {doc['event_date']}",
            f"- Site: {doc['site']}",
            f"- Asset ID: {doc['asset_id']}",
            f"- Technician: {doc['technician']}",
            f"- Category: {doc['issue_category']}",
            f"- Findings: {doc['failure_description']}",
            f"- Action Taken / Recommended: {doc['recommended_action']}",
            f"- Part Code: {doc['part_code']}",
            f"- Part Name: {doc['part_name']}",
            f"- Quantity: {doc['quantity']}",
            f"- Downtime Hours: {doc['downtime_hours']}",
            f"- Status: {doc['status']}",
        ]
    )


def render_vendor_request(doc: dict[str, str]) -> str:
    return "\n".join(
        [
            f"Subject: Service Request {doc['document_id']} for {doc['asset_id']}",
            f"Request Date: {doc['request_date']}",
            f"Required By: {doc['event_date']}",
            f"Site: {doc['site']}",
            f"Priority: {doc['priority']}",
            f"Vendor: {doc['vendor_name']}",
            f"Category: {doc['issue_category']}",
            f"Details: {doc['failure_description']}",
            f"Requested Action: {doc['recommended_action']}",
            f"Estimated Cost: {doc['estimated_cost']}",
            f"Status: {doc['status']}",
        ]
    )


def generate_all() -> None:
    for doc in WORK_ORDERS:
        write_text(INBOX_DIR / "work_orders" / f"{doc['document_id']}.txt", render_work_order(doc))
    for doc in TECHNICIAN_REPORTS:
        write_text(INBOX_DIR / "technician_reports" / f"{doc['document_id']}.md", render_technician_report(doc))
    write_csv(INBOX_DIR / "inspection_checklists" / "inspection_batch_a.csv", INSPECTION_ROWS)
    for doc in VENDOR_REQUESTS:
        write_text(INBOX_DIR / "vendor_requests" / f"{doc['document_id']}.txt", render_vendor_request(doc))
    write_csv(INBOX_DIR / "parts_requests" / "parts_requests_july.csv", PART_REQUESTS)
