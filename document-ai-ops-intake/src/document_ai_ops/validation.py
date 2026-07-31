from __future__ import annotations

from datetime import datetime

from .config import PRIORITY_ORDER, ROUTE_BY_CATEGORY, SITES, STATUS_ORDER


def parse_float(value: str) -> float | None:
    if not str(value).strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def is_valid_date(value: str) -> bool:
    if not value:
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_category(value: str) -> str:
    text = value.strip().lower()
    if text in {"mechanical", "electrical", "inspection", "instrumentation"}:
        return text
    if text in {"vendor_support", "vendor support"}:
        return "vendor_support"
    if text in {"procurement", "parts"}:
        return "procurement"
    return "general_ops"


def severity_score(priority: str, estimated_cost: float | None, downtime_hours: float | None) -> int:
    score = {"critical": 95, "high": 75, "medium": 55, "low": 35}.get(priority.lower(), 40)
    if estimated_cost and estimated_cost >= 10000:
        score += 5
    if downtime_hours and downtime_hours >= 4:
        score += 5
    return min(score, 100)


def validate_record(record: dict[str, str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    normalized = dict(record)
    issues: list[dict[str, str]] = []

    normalized["priority"] = normalized["priority"].strip().lower()
    normalized["status"] = normalized["status"].strip().lower()
    normalized["issue_category"] = normalize_category(normalized["issue_category"])
    normalized["site"] = normalized["site"].strip().upper()

    required_fields = ["document_id", "asset_id", "site", "priority", "issue_category", "status"]
    for field in required_fields:
        if not normalized[field].strip():
            issues.append({"field_name": field, "issue_type": "missing_required_field", "issue_detail": f"{field} is required"})

    if normalized["site"] and normalized["site"] not in SITES:
        issues.append({"field_name": "site", "issue_type": "invalid_site", "issue_detail": f"Unknown site {normalized['site']}"})
    if normalized["priority"] and normalized["priority"] not in PRIORITY_ORDER:
        issues.append({"field_name": "priority", "issue_type": "invalid_priority", "issue_detail": f"Unexpected priority {normalized['priority']}"})
    if normalized["status"] and normalized["status"] not in STATUS_ORDER:
        issues.append({"field_name": "status", "issue_type": "invalid_status", "issue_detail": f"Unexpected status {normalized['status']}"})

    for field in ["request_date", "event_date"]:
        if not is_valid_date(normalized[field]):
            issues.append({"field_name": field, "issue_type": "invalid_date", "issue_detail": f"Invalid date {normalized[field]}"})

    estimated_cost = parse_float(normalized["estimated_cost"])
    downtime_hours = parse_float(normalized["downtime_hours"])
    quantity = parse_float(normalized["quantity"])

    if normalized["estimated_cost"] and estimated_cost is None:
        issues.append({"field_name": "estimated_cost", "issue_type": "invalid_numeric", "issue_detail": "Estimated cost is not numeric"})
    if estimated_cost is not None and estimated_cost < 0:
        issues.append({"field_name": "estimated_cost", "issue_type": "negative_value", "issue_detail": "Estimated cost cannot be negative"})
    if normalized["downtime_hours"] and downtime_hours is None:
        issues.append({"field_name": "downtime_hours", "issue_type": "invalid_numeric", "issue_detail": "Downtime hours is not numeric"})
    if downtime_hours is not None and downtime_hours < 0:
        issues.append({"field_name": "downtime_hours", "issue_type": "negative_value", "issue_detail": "Downtime hours cannot be negative"})
    if normalized["quantity"] and quantity is None:
        issues.append({"field_name": "quantity", "issue_type": "invalid_numeric", "issue_detail": "Quantity is not numeric"})
    if quantity is not None and quantity < 0:
        issues.append({"field_name": "quantity", "issue_type": "negative_value", "issue_detail": "Quantity cannot be negative"})

    if not normalized["event_date"]:
        normalized["event_date"] = normalized["request_date"]

    normalized["normalized_issue_category"] = normalized["issue_category"]
    normalized["severity_score"] = str(severity_score(normalized["priority"], estimated_cost, downtime_hours))
    normalized["urgency_flag"] = "high" if normalized["priority"] in {"critical", "high"} else "normal"
    normalized["missing_information_flag"] = "yes" if any(issue["issue_type"] == "missing_required_field" for issue in issues) else "no"
    normalized["route_to_team"] = ROUTE_BY_CATEGORY.get(normalized["issue_category"], "operations_support")
    normalized["summary_for_business"] = (
        f"{normalized['document_type']} for {normalized['asset_id'] or 'unknown asset'} at {normalized['site'] or 'unknown site'} "
        f"with {normalized['priority'] or 'unclassified'} priority. {normalized['failure_description'] or 'No failure description provided.'}"
    )
    normalized["extraction_confidence"] = "0.92" if not issues else "0.61"
    normalized["is_exception"] = "yes" if issues else "no"
    return normalized, issues
