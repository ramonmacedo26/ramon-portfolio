from __future__ import annotations

import csv
import html
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    ALLOWED_PRIORITY,
    ALLOWED_TICKET_STATUS,
    ARCHITECTURE_FLOW_PATH,
    DASHBOARD_PATH,
    DB_PATH,
    OUTPUT_DIR,
    RAW_DIR,
    SITES,
    TECHNICIANS,
    WAREHOUSE_DIR,
)
from .generate_data import generate_all


PROJECT_TITLE = "Fabric Ops Analytics Platform"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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

        CREATE TABLE bronze_service_tickets (
            ticket_id TEXT,
            site_id TEXT,
            opened_date TEXT,
            priority TEXT,
            status TEXT,
            category TEXT,
            estimated_sla_hours TEXT,
            resolution_hours TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_technician_shifts (
            technician_id TEXT,
            site_id TEXT,
            shift_date TEXT,
            scheduled_hours TEXT,
            productive_hours TEXT,
            overtime_hours TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_downtime_events (
            event_id TEXT,
            site_id TEXT,
            event_date TEXT,
            downtime_hours TEXT,
            cause_group TEXT,
            ingested_at TEXT
        );

        CREATE TABLE bronze_cost_ledger (
            cost_id TEXT,
            site_id TEXT,
            event_date TEXT,
            cost_type TEXT,
            amount_usd TEXT,
            ingested_at TEXT
        );

        CREATE TABLE data_quality_issues (
            source_table TEXT,
            record_key TEXT,
            issue_type TEXT,
            issue_detail TEXT,
            severity TEXT
        );

        CREATE TABLE silver_service_tickets (
            ticket_id TEXT,
            site_id TEXT,
            opened_date TEXT,
            priority TEXT,
            status TEXT,
            category TEXT,
            estimated_sla_hours REAL,
            resolution_hours REAL,
            is_open INTEGER,
            sla_breached INTEGER,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_technician_shifts (
            technician_id TEXT,
            site_id TEXT,
            shift_date TEXT,
            scheduled_hours REAL,
            productive_hours REAL,
            overtime_hours REAL,
            utilization_pct REAL,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_downtime_events (
            event_id TEXT,
            site_id TEXT,
            event_date TEXT,
            downtime_hours REAL,
            cause_group TEXT,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE silver_cost_ledger (
            cost_id TEXT,
            site_id TEXT,
            event_date TEXT,
            cost_type TEXT,
            amount_usd REAL,
            is_valid INTEGER,
            quality_notes TEXT
        );

        CREATE TABLE gold_site_operations_summary (
            site_id TEXT PRIMARY KEY,
            site_name TEXT,
            region TEXT,
            open_tickets INTEGER,
            breached_sla_tickets INTEGER,
            backlog_risk_score INTEGER,
            avg_utilization_pct REAL,
            total_downtime_hours REAL,
            total_cost_usd REAL
        );

        CREATE TABLE gold_technician_capacity_summary (
            technician_id TEXT PRIMARY KEY,
            technician_name TEXT,
            site_id TEXT,
            specialty TEXT,
            avg_utilization_pct REAL,
            total_overtime_hours REAL,
            workload_tier TEXT
        );

        CREATE TABLE gold_priority_backlog_summary (
            priority TEXT PRIMARY KEY,
            open_ticket_count INTEGER,
            breached_ticket_count INTEGER
        );

        CREATE TABLE gold_exec_kpis (
            metric_name TEXT PRIMARY KEY,
            metric_value REAL,
            metric_label TEXT
        );
        """
    )
    return conn


def record_issue(
    conn: sqlite3.Connection,
    source_table: str,
    record_key: str,
    issue_type: str,
    issue_detail: str,
    severity: str = "warning",
) -> None:
    conn.execute(
        "INSERT INTO data_quality_issues VALUES (?, ?, ?, ?, ?)",
        (source_table, record_key, issue_type, issue_detail, severity),
    )


def insert_bronze(conn: sqlite3.Connection) -> None:
    ingested_at = utc_now()
    tickets = read_csv(RAW_DIR / "service_tickets.csv")
    shifts = read_csv(RAW_DIR / "technician_shifts.csv")
    downtime = read_csv(RAW_DIR / "downtime_events.csv")
    costs = read_csv(RAW_DIR / "cost_ledger.csv")

    execute_many(
        conn,
        "INSERT INTO bronze_service_tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["ticket_id"],
                row["site_id"],
                row["opened_date"],
                row["priority"],
                row["status"],
                row["category"],
                row["estimated_sla_hours"],
                row["resolution_hours"],
                ingested_at,
            )
            for row in tickets
        ],
    )
    execute_many(
        conn,
        "INSERT INTO bronze_technician_shifts VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["technician_id"],
                row["site_id"],
                row["shift_date"],
                row["scheduled_hours"],
                row["productive_hours"],
                row["overtime_hours"],
                ingested_at,
            )
            for row in shifts
        ],
    )
    execute_many(
        conn,
        "INSERT INTO bronze_downtime_events VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                row["event_id"],
                row["site_id"],
                row["event_date"],
                row["downtime_hours"],
                row["cause_group"],
                ingested_at,
            )
            for row in downtime
        ],
    )
    execute_many(
        conn,
        "INSERT INTO bronze_cost_ledger VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                row["cost_id"],
                row["site_id"],
                row["event_date"],
                row["cost_type"],
                row["amount_usd"],
                ingested_at,
            )
            for row in costs
        ],
    )
    conn.commit()


def build_silver_service_tickets(conn: sqlite3.Connection) -> None:
    rows = []
    for row in conn.execute("SELECT * FROM bronze_service_tickets ORDER BY opened_date, ticket_id"):
        notes = []
        if row["site_id"] not in SITES:
            notes.append("unknown site_id")
        if row["priority"] not in ALLOWED_PRIORITY:
            notes.append(f"invalid priority: {row['priority']}")
        if row["status"] not in ALLOWED_TICKET_STATUS:
            notes.append(f"invalid status: {row['status']}")
        estimated = as_float(row["estimated_sla_hours"])
        resolution = as_float(row["resolution_hours"])
        if estimated is None or estimated <= 0:
            notes.append("invalid estimated_sla_hours")
        if resolution is not None and resolution < 0:
            notes.append("negative resolution_hours")
        is_open = int(row["status"] in {"open", "in_progress"})
        sla_breached = int(is_open and estimated is not None and estimated <= 24 and row["priority"] in {"critical", "high"})
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "service_tickets", row["ticket_id"], "ticket_quality", "; ".join(notes))
        rows.append(
            (
                row["ticket_id"],
                row["site_id"],
                row["opened_date"],
                row["priority"],
                row["status"],
                row["category"],
                estimated,
                resolution,
                is_open,
                sla_breached,
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(
        conn,
        "INSERT INTO silver_service_tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def build_silver_technician_shifts(conn: sqlite3.Connection) -> None:
    rows = []
    for row in conn.execute("SELECT * FROM bronze_technician_shifts ORDER BY shift_date, technician_id"):
        notes = []
        scheduled = as_float(row["scheduled_hours"])
        productive = as_float(row["productive_hours"])
        overtime = as_float(row["overtime_hours"])
        if row["technician_id"] not in TECHNICIANS:
            notes.append("unknown technician_id")
        if row["site_id"] not in SITES:
            notes.append("unknown site_id")
        if scheduled is None or scheduled <= 0:
            notes.append("invalid scheduled_hours")
        if productive is None or productive < 0:
            notes.append("invalid productive_hours")
        if productive is not None and scheduled is not None and productive > scheduled + 4:
            notes.append("productive_hours unusually high")
        if overtime is None or overtime < 0:
            notes.append("invalid overtime_hours")
        utilization = None if scheduled in {None, 0} or productive is None else round(productive / scheduled * 100, 1)
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "technician_shifts", row["technician_id"] + "@" + row["shift_date"], "shift_quality", "; ".join(notes))
        rows.append(
            (
                row["technician_id"],
                row["site_id"],
                row["shift_date"],
                scheduled,
                productive,
                overtime,
                utilization,
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(
        conn,
        "INSERT INTO silver_technician_shifts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def build_silver_downtime_events(conn: sqlite3.Connection) -> None:
    rows = []
    for row in conn.execute("SELECT * FROM bronze_downtime_events ORDER BY event_date, event_id"):
        notes = []
        downtime = as_float(row["downtime_hours"])
        if row["site_id"] not in SITES:
            notes.append("unknown site_id")
        if downtime is None or downtime < 0:
            notes.append("invalid downtime_hours")
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "downtime_events", row["event_id"], "downtime_quality", "; ".join(notes))
        rows.append(
            (
                row["event_id"],
                row["site_id"],
                row["event_date"],
                downtime,
                row["cause_group"],
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(conn, "INSERT INTO silver_downtime_events VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()


def build_silver_cost_ledger(conn: sqlite3.Connection) -> None:
    rows = []
    for row in conn.execute("SELECT * FROM bronze_cost_ledger ORDER BY event_date, cost_id"):
        notes = []
        amount = as_float(row["amount_usd"])
        if row["site_id"] not in SITES:
            notes.append("unknown site_id")
        if amount is None or amount < 0:
            notes.append("invalid amount_usd")
        is_valid = 0 if notes else 1
        if notes:
            record_issue(conn, "cost_ledger", row["cost_id"], "cost_quality", "; ".join(notes))
        rows.append(
            (
                row["cost_id"],
                row["site_id"],
                row["event_date"],
                row["cost_type"],
                amount,
                is_valid,
                "; ".join(notes),
            )
        )
    execute_many(conn, "INSERT INTO silver_cost_ledger VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()


def workload_tier(utilization: float, overtime: float) -> str:
    if utilization >= 88 or overtime >= 18:
        return "stretched"
    if utilization >= 74:
        return "healthy"
    return "underused"


def build_gold_models(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM gold_site_operations_summary")
    conn.execute("DELETE FROM gold_technician_capacity_summary")
    conn.execute("DELETE FROM gold_priority_backlog_summary")
    conn.execute("DELETE FROM gold_exec_kpis")

    site_rows = []
    for site_id, meta in SITES.items():
        open_tickets = conn.execute(
            "SELECT COUNT(*) FROM silver_service_tickets WHERE is_valid = 1 AND site_id = ? AND is_open = 1",
            (site_id,),
        ).fetchone()[0]
        breached = conn.execute(
            "SELECT COUNT(*) FROM silver_service_tickets WHERE is_valid = 1 AND site_id = ? AND sla_breached = 1",
            (site_id,),
        ).fetchone()[0]
        avg_util = conn.execute(
            "SELECT AVG(utilization_pct) FROM silver_technician_shifts WHERE is_valid = 1 AND site_id = ?",
            (site_id,),
        ).fetchone()[0] or 0
        downtime = conn.execute(
            "SELECT SUM(downtime_hours) FROM silver_downtime_events WHERE is_valid = 1 AND site_id = ?",
            (site_id,),
        ).fetchone()[0] or 0
        total_cost = conn.execute(
            "SELECT SUM(amount_usd) FROM silver_cost_ledger WHERE is_valid = 1 AND site_id = ?",
            (site_id,),
        ).fetchone()[0] or 0
        risk_score = min(100, int(open_tickets * 2.3 + breached * 8 + avg_util * 0.35 + downtime * 0.8))
        site_rows.append(
            (
                site_id,
                meta["name"],
                meta["region"],
                open_tickets,
                breached,
                risk_score,
                round(avg_util, 1),
                round(downtime, 1),
                round(total_cost, 2),
            )
        )
    execute_many(conn, "INSERT INTO gold_site_operations_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", site_rows)

    tech_rows = []
    for technician_id, meta in TECHNICIANS.items():
        avg_util = conn.execute(
            "SELECT AVG(utilization_pct) FROM silver_technician_shifts WHERE is_valid = 1 AND technician_id = ?",
            (technician_id,),
        ).fetchone()[0] or 0
        overtime = conn.execute(
            "SELECT SUM(overtime_hours) FROM silver_technician_shifts WHERE is_valid = 1 AND technician_id = ?",
            (technician_id,),
        ).fetchone()[0] or 0
        tech_rows.append(
            (
                technician_id,
                meta["name"],
                meta["site_id"],
                meta["specialty"],
                round(avg_util, 1),
                round(overtime, 1),
                workload_tier(avg_util, overtime),
            )
        )
    execute_many(conn, "INSERT INTO gold_technician_capacity_summary VALUES (?, ?, ?, ?, ?, ?, ?)", tech_rows)

    priority_rows = []
    for priority in ["critical", "high", "medium", "low"]:
        open_count = conn.execute(
            "SELECT COUNT(*) FROM silver_service_tickets WHERE is_valid = 1 AND priority = ? AND is_open = 1",
            (priority,),
        ).fetchone()[0]
        breached_count = conn.execute(
            "SELECT COUNT(*) FROM silver_service_tickets WHERE is_valid = 1 AND priority = ? AND sla_breached = 1",
            (priority,),
        ).fetchone()[0]
        priority_rows.append((priority, open_count, breached_count))
    execute_many(conn, "INSERT INTO gold_priority_backlog_summary VALUES (?, ?, ?)", priority_rows)

    total_open = conn.execute(
        "SELECT SUM(open_tickets) FROM gold_site_operations_summary"
    ).fetchone()[0] or 0
    total_breached = conn.execute(
        "SELECT SUM(breached_sla_tickets) FROM gold_site_operations_summary"
    ).fetchone()[0] or 0
    total_downtime = conn.execute(
        "SELECT SUM(total_downtime_hours) FROM gold_site_operations_summary"
    ).fetchone()[0] or 0
    avg_util = conn.execute(
        "SELECT AVG(avg_utilization_pct) FROM gold_site_operations_summary"
    ).fetchone()[0] or 0
    exec_rows = [
        ("open_backlog", float(total_open), "Open backlog"),
        ("sla_breaches", float(total_breached), "Breached SLAs"),
        ("downtime_hours", float(round(total_downtime, 1)), "Downtime hours"),
        ("avg_utilization_pct", float(round(avg_util, 1)), "Avg utilization %"),
    ]
    execute_many(conn, "INSERT INTO gold_exec_kpis VALUES (?, ?, ?)", exec_rows)
    conn.commit()


def write_architecture_flow(output_path: Path = ARCHITECTURE_FLOW_PATH) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="560" viewBox="0 0 1400 560">
  <defs>
    <linearGradient id="hero" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0f2747"/>
      <stop offset="100%" stop-color="#1967a7"/>
    </linearGradient>
    <linearGradient id="arrow" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0%" stop-color="#0f766e"/>
      <stop offset="100%" stop-color="#1565c0"/>
    </linearGradient>
    <style>
      .title { font: 800 34px 'Segoe UI', Arial, sans-serif; fill: white; }
      .subtitle { font: 400 17px 'Segoe UI', Arial, sans-serif; fill: #dcecff; }
      .stepTitle { font: 800 20px 'Segoe UI', Arial, sans-serif; fill: #132238; }
      .stepBody { font: 500 15px 'Segoe UI', Arial, sans-serif; fill: #617083; }
      .mini { font: 700 12px 'Segoe UI', Arial, sans-serif; fill: #1565c0; letter-spacing: 1px; text-transform: uppercase; }
      .artifact { font: 700 15px 'Segoe UI', Arial, sans-serif; fill: #0f766e; }
    </style>
  </defs>
  <rect width="1400" height="560" fill="#edf3f8"/>
  <rect x="36" y="28" width="1328" height="108" rx="26" fill="url(#hero)"/>
  <text x="68" y="76" class="title">Fabric Ops Analytics Platform - End-to-End Flow</text>
  <text x="68" y="108" class="subtitle">Raw operational extracts to Bronze, Silver, Gold, and stakeholder-facing outputs</text>

  <rect x="52" y="186" width="250" height="220" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="76" y="220" class="mini">Inputs</text>
  <text x="76" y="254" class="stepTitle">Raw CSV extracts</text>
  <text x="76" y="286" class="stepBody">service_tickets.csv</text>
  <text x="76" y="314" class="stepBody">technician_shifts.csv</text>
  <text x="76" y="342" class="stepBody">downtime_events.csv</text>
  <text x="76" y="370" class="stepBody">cost_ledger.csv</text>

  <rect x="384" y="186" width="250" height="220" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="408" y="220" class="mini">Layer 1</text>
  <text x="408" y="254" class="stepTitle">Bronze ingestion</text>
  <text x="408" y="286" class="stepBody">Preserve source rows</text>
  <text x="408" y="314" class="stepBody">Minimal assumptions</text>
  <text x="408" y="342" class="stepBody">Create traceable raw tables</text>

  <rect x="716" y="186" width="250" height="220" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="740" y="220" class="mini">Layer 2</text>
  <text x="740" y="254" class="stepTitle">Silver validation</text>
  <text x="740" y="286" class="stepBody">Type conversion</text>
  <text x="740" y="314" class="stepBody">Business rule checks</text>
  <text x="740" y="342" class="stepBody">Quality issue logging</text>

  <rect x="1048" y="186" width="300" height="220" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="1072" y="220" class="mini">Layer 3</text>
  <text x="1072" y="254" class="stepTitle">Gold KPI models</text>
  <text x="1072" y="286" class="stepBody">Site operations summary</text>
  <text x="1072" y="314" class="stepBody">Technician capacity summary</text>
  <text x="1072" y="342" class="stepBody">Priority backlog summary</text>
  <text x="1072" y="370" class="stepBody">Executive KPI layer</text>

  <rect x="928" y="436" width="420" height="86" rx="18" fill="#f6fbfa" stroke="#b7ddd5"/>
  <text x="952" y="470" class="mini">Outputs</text>
  <text x="952" y="498" class="artifact">dashboard.html   |   case_summary.md   |   fabric_ops.db</text>

  <rect x="716" y="436" width="170" height="86" rx="18" fill="#f8f9fc" stroke="#d8e2ed"/>
  <text x="740" y="470" class="mini">Controls</text>
  <text x="740" y="498" class="stepBody">data_quality_issues</text>

  <line x1="302" y1="296" x2="384" y2="296" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="384,296 360,282 360,310" fill="#1565c0"/>
  <line x1="634" y1="296" x2="716" y2="296" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="716,296 692,282 692,310" fill="#1565c0"/>
  <line x1="966" y1="296" x2="1048" y2="296" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="1048,296 1024,282 1024,310" fill="#1565c0"/>
  <line x1="841" y1="406" x2="841" y2="436" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
  <line x1="1198" y1="406" x2="1198" y2="436" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def render_dashboard(conn: sqlite3.Connection, output_path: Path = DASHBOARD_PATH) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    kpis = list(conn.execute("SELECT * FROM gold_exec_kpis"))
    sites = list(conn.execute("SELECT * FROM gold_site_operations_summary ORDER BY backlog_risk_score DESC"))
    techs = list(
        conn.execute(
            "SELECT * FROM gold_technician_capacity_summary ORDER BY avg_utilization_pct DESC, total_overtime_hours DESC LIMIT 5"
        )
    )
    priorities = list(conn.execute("SELECT * FROM gold_priority_backlog_summary"))
    issues = list(
        conn.execute(
            "SELECT issue_type, COUNT(*) AS issue_count FROM data_quality_issues GROUP BY issue_type ORDER BY issue_count DESC"
        )
    )
    max_cost = max([row["total_cost_usd"] for row in sites] or [1])
    site_cost_chart = "\n".join(
        f"""
        <div class="site-line">
          <div>
            <strong>{html.escape(row['site_id'])}</strong>
            <span>{html.escape(row['site_name'])}</span>
          </div>
          <div class="hbar"><span style="width:{int((row['total_cost_usd'] / max_cost) * 100)}%"></span></div>
          <strong>${row['total_cost_usd']:,.0f}</strong>
        </div>
        """
        for row in sites
    )
    priority_chart = "\n".join(
        f"""
        <div class="priority-card {html.escape(row['priority'])}">
          <span>{html.escape(row['priority'].title())}</span>
          <strong>{row['open_ticket_count']}</strong>
          <small>{row['breached_ticket_count']} breached</small>
        </div>
        """
        for row in priorities
    )

    def bar(score: int) -> str:
        width = max(6, min(100, score))
        return f"<div class='bar'><span style='width:{width}%'></span></div>"

    site_rows = "\n".join(
        f"""
        <tr>
          <td><strong>{html.escape(row['site_id'])}</strong><br><span>{html.escape(row['site_name'])}</span></td>
          <td>{row['open_tickets']}</td>
          <td>{row['breached_sla_tickets']}</td>
          <td>{row['avg_utilization_pct']:.1f}%</td>
          <td>{row['total_downtime_hours']:.1f}</td>
          <td>${row['total_cost_usd']:,.0f}</td>
          <td><strong>{row['backlog_risk_score']}</strong>{bar(int(row['backlog_risk_score']))}</td>
        </tr>
        """
        for row in sites
    )
    tech_cards = "\n".join(
        f"""
        <article class="mini-card">
          <div class="mini-label">{html.escape(row['technician_id'])} - {html.escape(row['site_id'])}</div>
          <strong>{html.escape(row['technician_name'])}</strong>
          <p>{html.escape(row['specialty'])}</p>
          <p>{row['avg_utilization_pct']:.1f}% utilization | {row['total_overtime_hours']:.1f}h overtime</p>
        </article>
        """
        for row in techs
    )
    priority_rows = "\n".join(
        f"<li><strong>{html.escape(row['priority'])}</strong>: {row['open_ticket_count']} open, {row['breached_ticket_count']} breached</li>"
        for row in priorities
    )
    issue_rows = "\n".join(
        f"<li><strong>{html.escape(row['issue_type'])}</strong>: {row['issue_count']}</li>"
        for row in issues
    )
    kpi_cards = "\n".join(
        f"""
        <article class="card">
          <div class="label">{html.escape(row['metric_label'])}</div>
          <div class="metric">{int(row['metric_value']) if float(row['metric_value']).is_integer() else row['metric_value']}</div>
        </article>
        """
        for row in kpis
    )
    output_path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{PROJECT_TITLE}</title>
  <style>
    :root {{
      --ink: #17212d;
      --muted: #627182;
      --line: #d7e0e8;
      --blue: #0f8cff;
      --teal: #0c9d7d;
      --coral: #ff7b54;
      --sand: #ffcc70;
      --bg: #f4efe7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Segoe UI", Arial, sans-serif;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.45), rgba(255,255,255,0.2)),
        var(--bg);
      color: var(--ink);
      line-height: 1.45;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }}
    .hero {{
      background: linear-gradient(135deg, #17324d, #245c8d 55%, #1d876d);
      color: white;
      border-radius: 24px;
      padding: 32px;
      box-shadow: 0 16px 50px rgba(19, 34, 56, 0.18);
    }}
    .hero p {{ color: #deecfa; max-width: 760px; }}
    h1 {{ margin: 0 0 8px; font-size: 36px; letter-spacing: -0.03em; }}
    h2 {{ margin: 26px 0 12px; font-size: 22px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin: 18px 0;
    }}
    .card, .panel, .mini-card {{
      background: rgba(255, 252, 248, 0.92);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 8px 24px rgba(19, 34, 56, 0.06);
    }}
    .card {{ padding: 18px; }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .metric {{
      margin-top: 8px;
      font-size: 30px;
      font-weight: 800;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
    }}
    th, td {{
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      background: #f5f8fb;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    td span {{
      color: var(--muted);
      font-size: 13px;
    }}
    .bar {{
      height: 7px;
      background: #e8eef5;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 6px;
    }}
    .bar span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--teal), var(--blue));
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .triple {{
      display: grid;
      grid-template-columns: 0.95fr 1.05fr 0.9fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .panel {{
      overflow: hidden;
    }}
    .panel-content {{
      padding: 18px;
    }}
    .panel-content h3 {{
      margin: 18px 0 8px;
      font-size: 16px;
    }}
    .flow-image {{
      width: 100%;
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: white;
    }}
    .mini-grid {{
      display: grid;
      gap: 12px;
    }}
    .site-line {{
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .site-line span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .hbar {{
      height: 10px;
      background: #e8ddd2;
      border-radius: 999px;
      overflow: hidden;
    }}
    .hbar span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--coral), var(--sand));
    }}
    .priority-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .priority-card {{
      padding: 14px;
      border-radius: 16px;
      color: white;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .priority-card span {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .priority-card strong {{ font-size: 26px; }}
    .priority-card small {{ opacity: 0.9; }}
    .priority-card.critical {{ background: linear-gradient(135deg, #b93827, #ff7b54); }}
    .priority-card.high {{ background: linear-gradient(135deg, #d18a00, #ffb84d); }}
    .priority-card.medium {{ background: linear-gradient(135deg, #0f8cff, #57b0ff); }}
    .priority-card.low {{ background: linear-gradient(135deg, #0c9d7d, #3fc4a2); }}
    .mini-card {{
      padding: 16px;
    }}
    .mini-card p {{
      margin: 6px 0 0;
    }}
    .mini-label {{
      color: var(--blue);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
    }}
    footer {{
      margin-top: 22px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 920px) {{
      .cards, .grid, .triple, .priority-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <h1>{PROJECT_TITLE}</h1>
    <p>
      Portfolio case study for a Microsoft Fabric style operations analytics platform with Bronze,
      Silver, and Gold layers for backlog, SLA, downtime, workforce, and cost visibility.
    </p>
    <p><strong>Objective:</strong> turn disconnected service and maintenance extracts into a decision-ready operations scorecard.</p>
  </section>

  <section class="cards">
    {kpi_cards}
  </section>

  <section class="triple">
    <section class="panel">
      <div class="panel-content">
        <h2>How to read this dashboard</h2>
        <p>Start with global KPIs, compare site performance, then inspect backlog pressure, capacity strain, and quality gates.</p>
        <h3>Architecture</h3>
        <p>Raw extracts -> Bronze ingestion -> Silver validation -> Gold KPI models -> HTML scorecard.</p>
        <img class="flow-image" src="architecture_flow.svg" alt="Architecture flowchart from raw CSV extracts to Bronze, Silver, Gold, and final outputs.">
      </div>
    </section>
    <section class="panel">
      <div class="panel-content">
        <h2>Cost exposure by site</h2>
        <p>Shows where operational cost accumulation is building fastest across the network.</p>
        {site_cost_chart}
      </div>
    </section>
    <section class="panel">
      <div class="panel-content">
        <h2>Backlog by priority</h2>
        <div class="priority-grid">{priority_chart}</div>
      </div>
    </section>
  </section>

  <h2>Site operations summary</h2>
  <section class="panel">
    <table>
      <thead>
        <tr>
          <th>Site</th><th>Open backlog</th><th>SLA breaches</th><th>Avg utilization</th><th>Downtime</th><th>Cost</th><th>Risk</th>
        </tr>
      </thead>
      <tbody>{site_rows}</tbody>
    </table>
  </section>

  <section class="grid">
    <div>
      <h2>Top technician workload signals</h2>
      <div class="mini-grid">{tech_cards}</div>
    </div>
    <div>
      <h2>Backlog and data quality</h2>
      <section class="panel">
        <div class="panel-content">
          <p>This layer summarizes open work concentration by priority and highlights source issues caught before business consumption.</p>
          <h3>Priority backlog</h3>
          <ul>{priority_rows}</ul>
          <h3>Quality issues caught</h3>
          <ul>{issue_rows}</ul>
        </div>
      </section>
    </div>
  </section>

  <footer>Generated at {utc_now()} from local synthetic data. No client or employer data is included.</footer>
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
    sites = list(conn.execute("SELECT * FROM gold_site_operations_summary ORDER BY backlog_risk_score DESC"))
    issues = Counter(row["issue_type"] for row in conn.execute("SELECT issue_type FROM data_quality_issues"))
    output_path.write_text(
        "\n".join(
            [
                f"# {PROJECT_TITLE}",
                "",
                "## Recruiter Summary",
                "",
                "Built a local operations analytics demo that simulates a Microsoft Fabric style lakehouse workflow, from raw service extracts to Gold KPIs for backlog, SLA risk, technician utilization, downtime, and cost.",
                "",
                "## Highest Risk Sites",
                "",
                *[
                    f"- {row['site_id']} ({row['site_name']}): risk {row['backlog_risk_score']}, open backlog {row['open_tickets']}, breached SLAs {row['breached_sla_tickets']}"
                    for row in sites[:4]
                ],
                "",
                "## Data Quality Issues Caught",
                "",
                *[f"- {issue_type}: {count}" for issue_type, count in sorted(issues.items())],
                "",
                "## Stack",
                "",
                "Python, SQL, SQLite, medallion architecture, operations analytics, data quality checks, HTML scorecard.",
            ]
        ),
        encoding="utf-8",
    )
    return output_path


def run_pipeline(regenerate_data: bool = True) -> dict[str, str]:
    if regenerate_data:
        generate_all()
    conn = prepare_database()
    try:
        insert_bronze(conn)
        build_silver_service_tickets(conn)
        build_silver_technician_shifts(conn)
        build_silver_downtime_events(conn)
        build_silver_cost_ledger(conn)
        build_gold_models(conn)
        architecture = write_architecture_flow()
        dashboard = render_dashboard(conn)
        summary = write_case_summary(conn)
    finally:
        conn.close()
    return {
        "database": str(DB_PATH),
        "architecture_flow": str(architecture),
        "dashboard": str(dashboard),
        "summary": str(summary),
    }


def main() -> int:
    outputs = run_pipeline(regenerate_data=True)
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
