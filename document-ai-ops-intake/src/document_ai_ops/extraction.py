from __future__ import annotations

import csv
import re
from pathlib import Path

from .config import DOCUMENT_TYPES


KEY_PATTERNS = {
    "document_id": [r"^Work Order:\s*([^\r\n]*)", r"^# Technician Report\s+([^\r\n]*)", r"^Subject: Service Request\s+([^\r\n]+?)\s+for"],
    "asset_id": [r"^Asset ID:\s*([^\r\n]*)", r"^- Asset ID:\s*([^\r\n]*)", r"for\s+([A-Z]+-\d+)"],
    "asset_name": [r"^Asset Name:\s*([^\r\n]*)"],
    "site": [r"^Site:\s*([^\r\n]*)", r"^- Site:\s*([^\r\n]*)"],
    "request_date": [r"^Request Date:\s*([^\r\n]*)"],
    "event_date": [r"^- Event Date:\s*([^\r\n]*)", r"^Required By:\s*([^\r\n]*)"],
    "priority": [r"^Priority:\s*([^\r\n]*)", r"^- Priority:\s*([^\r\n]*)"],
    "issue_category": [r"^Category:\s*([^\r\n]*)", r"^- Category:\s*([^\r\n]*)"],
    "failure_description": [r"^Failure Description:\s*([^\r\n]*)", r"^- Findings:\s*([^\r\n]*)", r"^Details:\s*([^\r\n]*)"],
    "recommended_action": [r"^Recommended Action:\s*([^\r\n]*)", r"^- Action Taken / Recommended:\s*([^\r\n]*)", r"^Requested Action:\s*([^\r\n]*)"],
    "requester": [r"^Requester:\s*([^\r\n]*)"],
    "technician": [r"^- Technician:\s*([^\r\n]*)"],
    "vendor_name": [r"^Vendor:\s*([^\r\n]*)"],
    "part_code": [r"^- Part Code:\s*([^\r\n]*)"],
    "part_name": [r"^- Part Name:\s*([^\r\n]*)"],
    "quantity": [r"^- Quantity:\s*([^\r\n]*)"],
    "estimated_cost": [r"^Estimated Cost:\s*([^\r\n]*)"],
    "downtime_hours": [r"^Downtime Hours:\s*([^\r\n]*)", r"^- Downtime Hours:\s*([^\r\n]*)"],
    "status": [r"^Status:\s*([^\r\n]*)", r"^- Status:\s*([^\r\n]*)"],
}


def empty_record(document_type: str, source_file: str) -> dict[str, str]:
    return {
        "document_id": "",
        "document_type": document_type,
        "source_file": source_file,
        "asset_id": "",
        "asset_name": "",
        "site": "",
        "request_date": "",
        "event_date": "",
        "priority": "",
        "status": "",
        "issue_category": "",
        "failure_description": "",
        "recommended_action": "",
        "requester": "",
        "technician": "",
        "vendor_name": "",
        "part_code": "",
        "part_name": "",
        "quantity": "",
        "estimated_cost": "",
        "downtime_hours": "",
        "raw_text_excerpt": "",
    }


def find_value(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def extract_from_text(path: Path, document_type: str) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    record = empty_record(document_type, path.name)
    for key, patterns in KEY_PATTERNS.items():
        record[key] = find_value(text, patterns)
    record["raw_text_excerpt"] = " ".join(text.split())[:180]
    if document_type == DOCUMENT_TYPES["vendor_requests"] and not record["event_date"]:
        record["event_date"] = record["request_date"]
    if document_type == DOCUMENT_TYPES["technician_reports"] and not record["request_date"]:
        record["request_date"] = record["event_date"]
    return record


def extract_from_csv(path: Path, document_type: str) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    records: list[dict[str, str]] = []
    for row in rows:
        record = empty_record(document_type, path.name)
        record.update({key: value.strip() for key, value in row.items() if key in record and value is not None})
        record["raw_text_excerpt"] = " ".join(f"{key}={value}" for key, value in row.items())[:180]
        records.append(record)
    return records


def extract_documents(inbox_dir: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for folder_name, document_type in DOCUMENT_TYPES.items():
        folder = inbox_dir / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in {".txt", ".md"}:
                records.append(extract_from_text(path, document_type))
            elif path.suffix.lower() == ".csv":
                records.extend(extract_from_csv(path, document_type))
    return records
