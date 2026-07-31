from __future__ import annotations

import csv
import html
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    ALLOWED_PRIORITY,
    ALLOWED_WORK_ORDER_STATUS,
    DASHBOARD_PATH,
    DB_PATH,
    EQUIPMENT,
    OUTPUT_DIR,
    RAW_DIR,
    SENSOR_THRESHOLDS,
    WAREHOUSE_DIR,
)
from .generate_data import generate_all


PROJECT_TITLE = "Industrial Data & AI Copilot - Predictive Maintenance Analytics"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def execute_many(conn: sqlite3.Connection, sql: str, rows: list[tuple]) -> None:
    if rows:
        conn.executemany(sql, rows)


def prepare_database(db_path: Path = DB_PATH) -> sqlite3.Connection:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE bronze_sensor_readings (
            event_ts TEXT,
            equipment_id TEXT,
            temperature_c TEXT,
            vibration_mm_s TEXT,
            pressure_bar TEXT,
            energy_kwh TEXT,
            source_file TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_maintenance_orders (
            work_order_id TEXT,
            equipment_id TEXT,
            opened_at TEXT,
            closed_at TEXT,
            priority TEXT,
            status TEXT,
            description TEXT,
            source_file TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_cost_events (
            cost_id TEXT,
            event_date TEXT,
            equipment_id TEXT,
            category TEXT,
            amount_usd TEXT,
            source_file TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_work_reports (
            document_id TEXT,
            document_date TEXT,
            equipment_id TEXT,
            author TEXT,
            report_text TEXT,
            source_file TEXT,
            ingested_at TEXT
        );

        CREATE TABLE data_quality_issues (
            layer TEXT,
            source_table TEXT,
            record_key TEXT,
            issue_type TEXT,
            issue_detail TEXT,
            severity TEXT
        );

        CREATE TABLE silver_sensor_readings (
            event_ts TEXT,
            equipment_id TEXT,
            temperature_c REAL,
            vibration_mm_s REAL,
            pressure_bar REAL,
            energy_kwh REAL,
            temperature_anomaly INTEGER,
            vibration_anomaly INTEGER,
            pressure_anomaly INTEGER,
            energy_anomaly INTEGER,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_maintenance_orders (
            work_order_id TEXT,
            equipment_id TEXT,
            opened_at TEXT,
            closed_at TEXT,
            priority TEXT,
            status TEXT,
            description TEXT,
            is_open INTEGER,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_cost_events (
            cost_id TEXT,
            event_date TEXT,
            equipment_id TEXT,
            category TEXT,
            amount_usd REAL,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_work_reports (
            document_id TEXT,
            document_date TEXT,
            equipment_id TEXT,
            author TEXT,
            report_text TEXT,
            extracted_signals TEXT,
            severity_hint TEXT,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE gold_equipment_health_summary (
            equipment_id TEXT PRIMARY KEY,
            equipment_name TEXT,
            site TEXT,
            criticality TEXT,
            sensor_rows INTEGER,
            anomaly_count INTEGER,
            open_work_orders INTEGER,
            critical_or_high_work_orders INTEGER,
            total_cost_usd REAL,
            latest_report_signal TEXT,
            risk_score INTEGER,
            risk_tier TEXT
        );

        CREATE TABLE gold_work_order_copilot_briefs (
            work_order_id TEXT PRIMARY KEY,
            equipment_id TEXT,
            priority TEXT,
            status TEXT,
            root_signal TEXT,
            recommended_action TEXT,
            copilot_brief TEXT
        );
        """
    )
    return conn


def insert_bronze(conn: sqlite3.Connection) -> None:
    ingested_at = utc_now()
    sensors = read_csv(RAW_DIR / "sensor_readings.csv")
    work_orders = read_csv(RAW_DIR / "maintenance_orders.csv")
    costs = read_csv(RAW_DIR / "cost_events.csv")
    reports = read_csv(RAW_DIR / "work_reports.csv")

    execute_many(
        conn,
        """
        INSERT INTO bronze_sensor_readings
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["event_ts"],
                row["equipment_id"],
                row["temperature_c"],
                row["vibration_mm_s"],
                row["pressure_bar"],
                row["energy_kwh"],
                "sensor_readings.csv",
                ingested_at,
            )
            for row in sensors
        ],
    )
    execute_many(
        conn,
        """
        INSERT INTO bronze_maintenance_orders
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["work_order_id"],
                row["equipment_id"],
                row["opened_at"],
                row["closed_at"],
                row["priority"],
                row["status"],
                row["description"],
                "maintenance_orders.csv",
                ingested_at,
            )
            for row in work_orders
        ],
    )
    execute_many(
        conn,
        """
        INSERT INTO bronze_cost_events
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["cost_id"],
                row["event_date"],
                row["equipment_id"],
                row["category"],
                row["amount_usd"],
                "cost_events.csv",
                ingested_at,
            )
            for row in costs
        ],
    )
    execute_many(
        conn,
        """
        INSERT INTO bronze_work_reports
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["document_id"],
                row["document_date"],
                row["equipment_id"],
                row["author"],
                row["report_text"],
                "work_reports.csv",
                ingested_at,
            )
            for row in reports
        ],
    )
    conn.commit()


def record_issue(
    conn: sqlite3.Connection,
    layer: str,
    source_table: str,
    record_key: str,
    issue_type: str,
    issue_detail: str,
    severity: str = "warning",
) -> None:
    conn.execute(
        """
        INSERT INTO data_quality_issues
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (layer, source_table, record_key, issue_type, issue_detail, severity),
    )


def sensor_quality_notes(row: sqlite3.Row, seen_keys: set[tuple[str, str]]) -> tuple[int, str, dict[str, float | None]]:
    record_key = (row["event_ts"], row["equipment_id"])
    values = {
        "temperature_c": as_float(row["temperature_c"]),
        "vibration_mm_s": as_float(row["vibration_mm_s"]),
        "pressure_bar": as_float(row["pressure_bar"]),
        "energy_kwh": as_float(row["energy_kwh"]),
    }
    notes: list[str] = []
    if record_key in seen_keys:
        notes.append("duplicate equipment/timestamp")
    if row["equipment_id"] not in EQUIPMENT:
        notes.append("unknown equipment")
    for field, value in values.items():
        if value is None:
            notes.append(f"missing or invalid {field}")
    if values["pressure_bar"] is not None and values["pressure_bar"] > 100:
        notes.append("pressure value appears physically impossible")
    if values["temperature_c"] is not None and values["temperature_c"] < -20:
        notes.append("temperature value appears physically impossible")
    is_valid = 0 if notes else 1
    seen_keys.add(record_key)
    return is_valid, "; ".join(notes), values


def build_silver_sensor_readings(conn: sqlite3.Connection) -> None:
    seen_keys: set[tuple[str, str]] = set()
    rows_to_insert = []
    for row in conn.execute("SELECT * FROM bronze_sensor_readings ORDER BY event_ts, equipment_id"):
        is_valid, notes, values = sensor_quality_notes(row, seen_keys)
        record_key = f"{row['equipment_id']}@{row['event_ts']}"
        if notes:
            record_issue(conn, "silver", "sensor_readings", record_key, "sensor_quality", notes, "warning")

        temperature = values["temperature_c"]
        vibration = values["vibration_mm_s"]
        pressure = values["pressure_bar"]
        energy = values["energy_kwh"]
        temperature_anomaly = int(temperature is not None and temperature > SENSOR_THRESHOLDS["temperature_c_max"])
        vibration_anomaly = int(vibration is not None and vibration > SENSOR_THRESHOLDS["vibration_mm_s_max"])
        pressure_anomaly = int(
            pressure is not None
            and (
                pressure < SENSOR_THRESHOLDS["pressure_bar_min"]
                or pressure > SENSOR_THRESHOLDS["pressure_bar_max"]
            )
        )
        energy_anomaly = int(energy is not None and energy > SENSOR_THRESHOLDS["energy_kwh_max"])
        rows_to_insert.append(
            (
                row["event_ts"],
                row["equipment_id"],
                temperature,
                vibration,
                pressure,
                energy,
                temperature_anomaly,
                vibration_anomaly,
                pressure_anomaly,
                energy_anomaly,
                is_valid,
                notes,
            )
        )
    execute_many(
        conn,
        """
        INSERT INTO silver_sensor_readings
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def build_silver_maintenance_orders(conn: sqlite3.Connection) -> None:
    rows_to_insert = []
    for row in conn.execute("SELECT * FROM bronze_maintenance_orders ORDER BY opened_at"):
        notes = []
        if row["equipment_id"] not in EQUIPMENT:
            notes.append("unknown equipment")
        if row["status"] not in ALLOWED_WORK_ORDER_STATUS:
            notes.append(f"unexpected status: {row['status']}")
        if row["priority"] not in ALLOWED_PRIORITY:
            notes.append(f"unexpected priority: {row['priority']}")
        if row["closed_at"] and row["closed_at"] < row["opened_at"]:
            notes.append("closed_at precedes opened_at")
        is_valid = 0 if notes else 1
        if notes:
            record_issue(
                conn,
                "silver",
                "maintenance_orders",
                row["work_order_id"],
                "work_order_quality",
                "; ".join(notes),
                "warning",
            )
        rows_to_insert.append(
            (
                row["work_order_id"],
                row["equipment_id"],
                row["opened_at"],
                row["closed_at"],
                row["priority"],
                row["status"],
                row["description"],
                int(row["status"] in {"open", "in_progress"}),
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(
        conn,
        """
        INSERT INTO silver_maintenance_orders
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def build_silver_cost_events(conn: sqlite3.Connection) -> None:
    rows_to_insert = []
    for row in conn.execute("SELECT * FROM bronze_cost_events ORDER BY event_date"):
        amount = as_float(row["amount_usd"])
        notes = []
        if row["equipment_id"] not in EQUIPMENT:
            notes.append("unknown equipment")
        if amount is None or amount < 0:
            notes.append("invalid amount_usd")
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "silver", "cost_events", row["cost_id"], "cost_quality", "; ".join(notes), "warning")
        rows_to_insert.append(
            (
                row["cost_id"],
                row["event_date"],
                row["equipment_id"],
                row["category"],
                amount,
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(
        conn,
        """
        INSERT INTO silver_cost_events
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def extract_report_signals(report_text: str) -> tuple[list[str], str]:
    text = report_text.lower()
    signal_map = {
        "vibration": ["vibration", "bearing", "alignment"],
        "pressure": ["pressure", "valve", "restriction"],
        "temperature": ["temperature", "heat"],
        "energy": ["energy", "battery", "load transfer"],
        "leak/fouling": ["leak", "fouling", "cleaning"],
    }
    signals = [label for label, terms in signal_map.items() if any(term in text for term in terms)]
    severity = "high" if any(term in text for term in ["urgent", "abnormal", "spike", "high vibration"]) else "medium"
    if any(term in text for term in ["completed", "no leak detected", "routine"]):
        severity = "low"
    return signals or ["general inspection"], severity


def build_silver_work_reports(conn: sqlite3.Connection) -> None:
    rows_to_insert = []
    for row in conn.execute("SELECT * FROM bronze_work_reports ORDER BY document_date"):
        notes = []
        if row["equipment_id"] not in EQUIPMENT:
            notes.append("unknown equipment")
        if not row["report_text"].strip():
            notes.append("empty report_text")
        signals, severity = extract_report_signals(row["report_text"])
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "silver", "work_reports", row["document_id"], "report_quality", "; ".join(notes), "warning")
        rows_to_insert.append(
            (
                row["document_id"],
                row["document_date"],
                row["equipment_id"],
                row["author"],
                row["report_text"],
                ", ".join(signals),
                severity,
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(
        conn,
        """
        INSERT INTO silver_work_reports
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def tier_from_score(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "watch"
    if score >= 25:
        return "moderate"
    return "healthy"


def build_gold_equipment_summary(conn: sqlite3.Connection) -> None:
    sensor_stats = defaultdict(lambda: {"rows": 0, "anomalies": 0})
    for row in conn.execute(
        """
        SELECT equipment_id,
               COUNT(*) AS sensor_rows,
               SUM(temperature_anomaly + vibration_anomaly + pressure_anomaly + energy_anomaly) AS anomaly_count
        FROM silver_sensor_readings
        WHERE is_valid = 1
        GROUP BY equipment_id
        """
    ):
        sensor_stats[row["equipment_id"]] = {
            "rows": row["sensor_rows"] or 0,
            "anomalies": row["anomaly_count"] or 0,
        }

    work_order_stats = defaultdict(lambda: {"open": 0, "high": 0})
    for row in conn.execute(
        """
        SELECT equipment_id,
               SUM(is_open) AS open_work_orders,
               SUM(CASE WHEN priority IN ('critical','high') AND is_valid = 1 THEN 1 ELSE 0 END) AS high_priority
        FROM silver_maintenance_orders
        GROUP BY equipment_id
        """
    ):
        work_order_stats[row["equipment_id"]] = {
            "open": row["open_work_orders"] or 0,
            "high": row["high_priority"] or 0,
        }

    cost_stats = defaultdict(float)
    for row in conn.execute(
        """
        SELECT equipment_id, SUM(amount_usd) AS total_cost
        FROM silver_cost_events
        WHERE is_valid = 1
        GROUP BY equipment_id
        """
    ):
        cost_stats[row["equipment_id"]] = row["total_cost"] or 0

    latest_report = {}
    for row in conn.execute(
        """
        SELECT equipment_id, extracted_signals
        FROM silver_work_reports
        WHERE is_valid = 1
        ORDER BY document_date
        """
    ):
        latest_report[row["equipment_id"]] = row["extracted_signals"]

    rows_to_insert = []
    for equipment_id, meta in EQUIPMENT.items():
        sensor_rows = sensor_stats[equipment_id]["rows"]
        anomaly_count = sensor_stats[equipment_id]["anomalies"]
        open_work_orders = work_order_stats[equipment_id]["open"]
        high_priority = work_order_stats[equipment_id]["high"]
        total_cost = cost_stats[equipment_id]
        criticality_bonus = 12 if meta["criticality"] == "high" else 5
        risk_score = min(
            100,
            int(
                anomaly_count * 4.5
                + open_work_orders * 16
                + high_priority * 14
                + min(total_cost / 1000, 15) * 2
                + criticality_bonus
            ),
        )
        rows_to_insert.append(
            (
                equipment_id,
                meta["name"],
                meta["site"],
                meta["criticality"],
                sensor_rows,
                anomaly_count,
                open_work_orders,
                high_priority,
                round(total_cost, 2),
                latest_report.get(equipment_id, "no recent report"),
                risk_score,
                tier_from_score(risk_score),
            )
        )

    execute_many(
        conn,
        """
        INSERT INTO gold_equipment_health_summary
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def build_gold_work_order_briefs(conn: sqlite3.Connection) -> None:
    latest_signals = {
        row["equipment_id"]: row["extracted_signals"]
        for row in conn.execute(
            """
            SELECT equipment_id, extracted_signals
            FROM silver_work_reports
            WHERE is_valid = 1
            ORDER BY document_date
            """
        )
    }
    rows_to_insert = []
    for row in conn.execute(
        """
        SELECT *
        FROM silver_maintenance_orders
        WHERE is_valid = 1 AND is_open = 1
        ORDER BY
          CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
          opened_at
        """
    ):
        signal = latest_signals.get(row["equipment_id"], "general maintenance signal")
        if row["priority"] == "critical":
            action = "Escalate today; align maintenance, operations, and parts availability before next production window."
        elif row["priority"] == "high":
            action = "Schedule priority inspection and confirm whether sensor anomalies persist after intervention."
        else:
            action = "Monitor trend and close loop with maintenance notes after inspection."
        brief = (
            f"{row['equipment_id']} has an open {row['priority']} work order. "
            f"Detected signal: {signal}. Recommended action: {action}"
        )
        rows_to_insert.append(
            (
                row["work_order_id"],
                row["equipment_id"],
                row["priority"],
                row["status"],
                signal,
                action,
                brief,
            )
        )
    execute_many(
        conn,
        """
        INSERT INTO gold_work_order_copilot_briefs
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()


def build_silver_and_gold(conn: sqlite3.Connection) -> None:
    build_silver_sensor_readings(conn)
    build_silver_maintenance_orders(conn)
    build_silver_cost_events(conn)
    build_silver_work_reports(conn)
    build_gold_equipment_summary(conn)
    build_gold_work_order_briefs(conn)


def fetch_all(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return list(conn.execute(sql))


def render_bar(value: int, max_value: int = 100) -> str:
    width = max(4, min(100, int(value / max_value * 100)))
    return f"<div class='bar'><span style='width:{width}%'></span></div>"


def render_dashboard(conn: sqlite3.Connection, output_path: Path = DASHBOARD_PATH) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = fetch_all(
        conn,
        """
        SELECT *
        FROM gold_equipment_health_summary
        ORDER BY risk_score DESC
        """,
    )
    quality_rows = fetch_all(
        conn,
        """
        SELECT issue_type, severity, COUNT(*) AS issue_count
        FROM data_quality_issues
        GROUP BY issue_type, severity
        ORDER BY issue_count DESC
        """,
    )
    brief_rows = fetch_all(
        conn,
        """
        SELECT *
        FROM gold_work_order_copilot_briefs
        ORDER BY
          CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END
        """,
    )

    total_cost = sum(float(row["total_cost_usd"]) for row in summary_rows)
    open_orders = sum(int(row["open_work_orders"]) for row in summary_rows)
    anomaly_count = sum(int(row["anomaly_count"]) for row in summary_rows)
    highest_risk = summary_rows[0] if summary_rows else None
    tier_counts = Counter(row["risk_tier"] for row in summary_rows)
    signal_counts = Counter()
    for row in summary_rows:
        for signal in str(row["latest_report_signal"]).split(","):
            cleaned = signal.strip()
            if cleaned:
                signal_counts[cleaned] += 1

    top_assets = summary_rows[:5]
    max_risk = max([int(row["risk_score"]) for row in top_assets] or [1])
    asset_chart = "\n".join(
        f"""
        <div class="chart-row">
          <div>
            <strong>{html.escape(row['equipment_id'])}</strong>
            <span>{html.escape(row['equipment_name'])}</span>
          </div>
          <div class="chart-bar"><span style="width:{int(int(row['risk_score']) / max_risk * 100)}%"></span></div>
          <strong>{row['risk_score']}</strong>
        </div>
        """
        for row in top_assets
    )
    signal_chart = "\n".join(
        f"""
        <div class="signal-row">
          <span>{html.escape(name)}</span>
          <div class="signal-track"><span style="width:{count * 18}%"></span></div>
          <strong>{count}</strong>
        </div>
        """
        for name, count in signal_counts.most_common(5)
    )
    tier_badges = "".join(
        f"<div class='tier-card {html.escape(tier)}'><span>{html.escape(tier.title())}</span><strong>{count}</strong></div>"
        for tier, count in sorted(tier_counts.items())
    )

    equipment_rows_html = "\n".join(
        f"""
        <tr>
            <td><strong>{html.escape(row['equipment_id'])}</strong><br><span>{html.escape(row['equipment_name'])}</span></td>
            <td>{html.escape(row['site'])}</td>
            <td>{html.escape(row['criticality'])}</td>
            <td>{row['anomaly_count']}</td>
            <td>{row['open_work_orders']}</td>
            <td>${row['total_cost_usd']:,.0f}</td>
            <td><strong>{row['risk_score']}</strong>{render_bar(row['risk_score'])}<span class='tier {html.escape(row['risk_tier'])}'>{html.escape(row['risk_tier'])}</span></td>
        </tr>
        """
        for row in summary_rows
    )
    quality_html = "\n".join(
        f"<li><strong>{html.escape(row['issue_type'])}</strong>: {row['issue_count']} {html.escape(row['severity'])} issue(s)</li>"
        for row in quality_rows
    )
    briefs_html = "\n".join(
        f"""
        <article class='brief'>
            <div class='brief-topline'>{html.escape(row['work_order_id'])} · {html.escape(row['equipment_id'])} · {html.escape(row['priority'])}</div>
            <p>{html.escape(row['copilot_brief'])}</p>
        </article>
        """
        for row in brief_rows
    )
    generated_at = utc_now()
    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(PROJECT_TITLE)}</title>
  <style>
    :root {{
      --ink: #f4f8fb;
      --muted: #8ea3b7;
      --panel: #10263f;
      --panel-2: #173553;
      --blue: #52b6ff;
      --teal: #3dd6c6;
      --amber: #ffb648;
      --border: rgba(132, 179, 220, 0.18);
      --critical: #ff6b6b;
      --watch: #ffb648;
      --moderate: #52b6ff;
      --healthy: #34d399;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(61, 214, 198, 0.15), transparent 22%),
        radial-gradient(circle at top right, rgba(82, 182, 255, 0.18), transparent 24%),
        #071522;
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
      line-height: 1.45;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(16, 38, 63, 0.96), rgba(23, 53, 83, 0.94));
      border-radius: 24px;
      padding: 34px;
      border: 1px solid var(--border);
      box-shadow: 0 22px 60px rgba(0, 0, 0, 0.3);
    }}
    .hero p {{ max-width: 820px; color: #d5e5f4; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: -0.03em; }}
    h2 {{ margin: 28px 0 12px; font-size: 22px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0 8px;
    }}
    .card, .panel, .brief, .tier-card {{
      background: linear-gradient(180deg, rgba(16, 38, 63, 0.95), rgba(10, 24, 39, 0.95));
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 12px 34px rgba(0, 0, 0, 0.22);
    }}
    .card {{ padding: 18px; }}
    .label {{ color: var(--muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .metric {{ font-size: 28px; font-weight: 800; margin-top: 6px; }}
    .panel {{ overflow: hidden; }}
    table {{ width: 100%; border-collapse: collapse; background: transparent; }}
    th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.07em; background: rgba(82, 182, 255, 0.06); }}
    td span {{ color: var(--muted); font-size: 13px; }}
    .bar {{ height: 7px; margin: 6px 0; background: rgba(143, 173, 201, 0.14); border-radius: 99px; overflow: hidden; }}
    .bar span {{ display: block; height: 100%; background: linear-gradient(90deg, var(--teal), var(--blue)); border-radius: inherit; }}
    .tier {{ display: inline-flex; padding: 3px 8px; border-radius: 99px; color: white; font-size: 12px; }}
    .critical {{ background: var(--critical); }}
    .watch {{ background: var(--watch); }}
    .moderate {{ background: var(--moderate); }}
    .healthy {{ background: var(--healthy); }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .triple {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .panel-content {{ padding: 18px; }}
    .brief {{ padding: 16px; margin-bottom: 12px; }}
    .brief p {{ margin: 8px 0 0; }}
    .brief-topline {{ color: var(--amber); font-weight: 800; }}
    .chart-row, .signal-row {{
      display: grid;
      grid-template-columns: 1.1fr 1fr auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .chart-row span, .signal-row span {{ display: block; color: var(--muted); font-size: 13px; }}
    .chart-bar, .signal-track {{
      height: 10px;
      background: rgba(143, 173, 201, 0.12);
      border-radius: 999px;
      overflow: hidden;
    }}
    .chart-bar span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--amber), var(--critical));
    }}
    .signal-track span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--teal), var(--blue));
    }}
    .tier-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .tier-card {{ padding: 14px; text-align: center; }}
    .tier-card span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .tier-card strong {{ font-size: 24px; }}
    footer {{ margin-top: 24px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 900px) {{
      .cards, .grid, .triple, .tier-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <h1>{html.escape(PROJECT_TITLE)}</h1>
    <p>
      Portfolio case study showing a practical industrial data pipeline: synthetic operational data,
      quality checks, Bronze/Silver/Gold modeling, maintenance risk scoring, and AI-style work order briefs.
    </p>
    <div class="tier-grid">{tier_badges}</div>
  </section>

  <section class="cards">
    <div class="card"><div class="label">Open work orders</div><div class="metric">{open_orders}</div></div>
    <div class="card"><div class="label">Sensor anomalies</div><div class="metric">{anomaly_count}</div></div>
    <div class="card"><div class="label">Tracked costs</div><div class="metric">${total_cost:,.0f}</div></div>
    <div class="card"><div class="label">Highest risk asset</div><div class="metric">{html.escape(highest_risk['equipment_id']) if highest_risk else 'n/a'}</div></div>
  </section>

  <h2>Gold Equipment Health Summary</h2>
  <section class="panel">
    <table>
      <thead>
        <tr>
          <th>Equipment</th><th>Site</th><th>Criticality</th><th>Anomalies</th><th>Open WOs</th><th>Cost</th><th>Risk</th>
        </tr>
      </thead>
      <tbody>{equipment_rows_html}</tbody>
    </table>
  </section>

  <section class="triple">
    <div>
      <h2>Top risk concentration</h2>
      <section class="panel"><div class="panel-content">
        <p>These assets accumulate the heaviest combination of anomalies, open work, and cost exposure.</p>
        {asset_chart}
      </div></section>
    </div>
    <div>
      <h2>AI Copilot Work Order Briefs</h2>
      {briefs_html}
    </div>
    <div>
      <h2>Dominant maintenance signals</h2>
      <section class="panel"><div class="panel-content">
        <p>Recent reports were summarized into recurring signals to surface what maintenance teams should inspect first.</p>
        {signal_chart}
      </div></section>
      <h2>Data Quality Checks</h2>
      <section class="panel"><div class="panel-content">
        <p>This layer catches duplicated sensor records, missing values, physically impossible measurements, and invalid workflow statuses before analytics consumption.</p>
        <ul>{quality_html}</ul>
      </div></section>
    </div>
  </section>

  <section class="grid">
    <div>
      <h2>Reading the dashboard</h2>
      <section class="panel"><div class="panel-content">
        <p>Start with the KPI cards, move to the asset table, then inspect brief summaries and signal concentration to understand why each asset is trending into risk.</p>
      </div></section>
    </div>
    <div>
      <h2>Data Quality Checks</h2>
      <section class="panel"><div class="panel-content">
        <p>The quality layer acts as a control gate before recommendations and rankings are shown to stakeholders.</p>
        <ul>{quality_html}</ul>
      </div></section>
    </div>
  </section>

  <footer>Generated at {html.escape(generated_at)} from local synthetic data. No client or employer data is included.</footer>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return output_path


def write_case_summary(conn: sqlite3.Connection) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "case_summary.md"
    top_assets = fetch_all(
        conn,
        """
        SELECT equipment_id, equipment_name, risk_score, risk_tier, latest_report_signal
        FROM gold_equipment_health_summary
        ORDER BY risk_score DESC
        """
    )
    issues = Counter(
        row["issue_type"]
        for row in conn.execute("SELECT issue_type FROM data_quality_issues")
    )
    output_path.write_text(
        "\n".join(
            [
                f"# {PROJECT_TITLE}",
                "",
                "## Recruiter Summary",
                "",
                "Built a local industrial analytics demo that turns raw operational CSV files into a governed SQLite warehouse, quality-controlled Silver tables, Gold risk summaries, and AI-style work-order recommendations.",
                "",
                "## Highest Risk Assets",
                "",
                *[
                    f"- {row['equipment_id']} ({row['equipment_name']}): {row['risk_score']}/100, {row['risk_tier']} - {row['latest_report_signal']}"
                    for row in top_assets
                ],
                "",
                "## Data Quality Issues Caught",
                "",
                *[f"- {issue_type}: {count}" for issue_type, count in sorted(issues.items())],
                "",
                "## Stack",
                "",
                "Python, SQL, SQLite, data quality checks, Bronze/Silver/Gold modeling, HTML dashboard, rule-based AI copilot summaries.",
            ]
        ),
        encoding="utf-8",
    )
    return output_path


def write_dashboard_preview_svg(conn: sqlite3.Connection) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "dashboard_preview.svg"
    rows = fetch_all(
        conn,
        """
        SELECT equipment_id, equipment_name, risk_score, risk_tier, anomaly_count, open_work_orders
        FROM gold_equipment_health_summary
        ORDER BY risk_score DESC
        """
    )
    max_score = max([row["risk_score"] for row in rows] or [100])
    tier_colors = {
        "critical": "#b42318",
        "watch": "#b54708",
        "moderate": "#175cd3",
        "healthy": "#027a48",
    }
    bars = []
    for index, row in enumerate(rows):
        y = 210 + index * 72
        width = int((row["risk_score"] / max_score) * 500)
        color = tier_colors.get(row["risk_tier"], "#155c9d")
        bars.append(
            f"""
  <text x="72" y="{y}" class="asset">{html.escape(row['equipment_id'])} - {html.escape(row['equipment_name'])}</text>
  <rect x="72" y="{y + 16}" width="500" height="18" rx="9" fill="#e7edf4"/>
  <rect x="72" y="{y + 16}" width="{width}" height="18" rx="9" fill="{color}"/>
  <text x="595" y="{y + 30}" class="score">{row['risk_score']}/100 · {html.escape(row['risk_tier'])} · {row['anomaly_count']} anomalies · {row['open_work_orders']} open WOs</text>
"""
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620">
  <defs>
    <linearGradient id="hero" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0b2545"/>
      <stop offset="100%" stop-color="#1665ad"/>
    </linearGradient>
    <style>
      .title {{ font: 800 38px 'Segoe UI', Arial, sans-serif; fill: white; }}
      .subtitle {{ font: 400 18px 'Segoe UI', Arial, sans-serif; fill: #dcecff; }}
      .label {{ font: 700 13px 'Segoe UI', Arial, sans-serif; fill: #5f6b7a; letter-spacing: 1px; }}
      .metric {{ font: 800 34px 'Segoe UI', Arial, sans-serif; fill: #102033; }}
      .section {{ font: 800 24px 'Segoe UI', Arial, sans-serif; fill: #102033; }}
      .asset {{ font: 700 16px 'Segoe UI', Arial, sans-serif; fill: #102033; }}
      .score {{ font: 600 15px 'Segoe UI', Arial, sans-serif; fill: #5f6b7a; }}
    </style>
  </defs>
  <rect width="1200" height="620" fill="#eef3f8"/>
  <rect x="40" y="38" width="1120" height="126" rx="24" fill="url(#hero)"/>
  <text x="72" y="90" class="title">{html.escape(PROJECT_TITLE)}</text>
  <text x="72" y="126" class="subtitle">Bronze/Silver/Gold pipeline · data quality checks · risk scoring · AI-style work-order briefs</text>
  <rect x="60" y="186" width="1080" height="376" rx="22" fill="white" stroke="#d9e4ef"/>
  <text x="72" y="220" class="section">Equipment health summary</text>
  {''.join(bars)}
  <text x="72" y="586" class="score">Generated from synthetic local data. No employer/client data included.</text>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def run_pipeline(regenerate_data: bool = True) -> dict[str, str]:
    if regenerate_data:
        generate_all()
    conn = prepare_database()
    try:
        insert_bronze(conn)
        build_silver_and_gold(conn)
        dashboard = render_dashboard(conn)
        summary = write_case_summary(conn)
        preview = write_dashboard_preview_svg(conn)
    finally:
        conn.close()
    return {
        "database": str(DB_PATH),
        "dashboard": str(dashboard),
        "summary": str(summary),
        "preview": str(preview),
    }


def main() -> int:
    outputs = run_pipeline(regenerate_data=True)
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
