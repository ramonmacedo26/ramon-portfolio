from __future__ import annotations

import html
import json
import sqlite3
from collections import Counter
from pathlib import Path

from .config import (
    ARCHITECTURE_FLOW_PATH,
    CASE_SUMMARY_PATH,
    DASHBOARD_PATH,
    DB_PATH,
    EXCEPTIONS_CSV_PATH,
    EXCEPTIONS_XLSX_PATH,
    INBOX_DIR,
    MASTER_CSV_PATH,
    MASTER_XLSX_PATH,
    OUTPUT_DIR,
    VALIDATION_CSV_PATH,
    WAREHOUSE_DIR,
)
from .export import utc_now, write_csv, write_simple_xlsx
from .extraction import extract_documents
from .generate_data import generate_all
from .validation import validate_record


PROJECT_TITLE = "Document AI Ops Intake"

MASTER_FIELDS = [
    "document_id",
    "document_type",
    "source_file",
    "asset_id",
    "asset_name",
    "site",
    "request_date",
    "event_date",
    "priority",
    "status",
    "issue_category",
    "failure_description",
    "recommended_action",
    "requester",
    "technician",
    "vendor_name",
    "part_code",
    "part_name",
    "quantity",
    "estimated_cost",
    "downtime_hours",
    "normalized_issue_category",
    "severity_score",
    "urgency_flag",
    "missing_information_flag",
    "summary_for_business",
    "route_to_team",
    "extraction_confidence",
    "raw_text_excerpt",
]

ISSUE_FIELDS = ["document_id", "document_type", "source_file", "field_name", "issue_type", "issue_detail"]


def prepare_database(db_path: Path = DB_PATH) -> sqlite3.Connection:
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        DROP TABLE IF EXISTS bronze_documents;
        DROP TABLE IF EXISTS silver_document_records;
        DROP TABLE IF EXISTS validation_issues;

        CREATE TABLE bronze_documents (
            document_id TEXT,
            document_type TEXT,
            source_file TEXT,
            asset_id TEXT,
            site TEXT,
            priority TEXT,
            status TEXT,
            raw_text_excerpt TEXT
        );

        CREATE TABLE silver_document_records (
            document_id TEXT,
            document_type TEXT,
            source_file TEXT,
            asset_id TEXT,
            asset_name TEXT,
            site TEXT,
            request_date TEXT,
            event_date TEXT,
            priority TEXT,
            status TEXT,
            issue_category TEXT,
            failure_description TEXT,
            recommended_action TEXT,
            requester TEXT,
            technician TEXT,
            vendor_name TEXT,
            part_code TEXT,
            part_name TEXT,
            quantity TEXT,
            estimated_cost TEXT,
            downtime_hours TEXT,
            normalized_issue_category TEXT,
            severity_score TEXT,
            urgency_flag TEXT,
            missing_information_flag TEXT,
            summary_for_business TEXT,
            route_to_team TEXT,
            extraction_confidence TEXT,
            raw_text_excerpt TEXT,
            is_exception TEXT
        );

        CREATE TABLE validation_issues (
            document_id TEXT,
            document_type TEXT,
            source_file TEXT,
            field_name TEXT,
            issue_type TEXT,
            issue_detail TEXT
        );
        """
    )
    return conn


def insert_bronze(conn: sqlite3.Connection, records: list[dict[str, str]]) -> None:
    conn.executemany(
        "INSERT INTO bronze_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["document_id"],
                row["document_type"],
                row["source_file"],
                row["asset_id"],
                row["site"],
                row["priority"],
                row["status"],
                row["raw_text_excerpt"],
            )
            for row in records
        ],
    )
    conn.commit()


def build_silver(conn: sqlite3.Connection, records: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    master_rows: list[dict[str, str]] = []
    exception_rows: list[dict[str, str]] = []
    issue_rows: list[dict[str, str]] = []

    for record in records:
        normalized, issues = validate_record(record)
        silver_row = {field: normalized.get(field, "") for field in MASTER_FIELDS}
        silver_row["is_exception"] = normalized["is_exception"]
        conn.execute(
            "INSERT INTO silver_document_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(silver_row[field] for field in MASTER_FIELDS) + (silver_row["is_exception"],),
        )
        master_rows.append({field: silver_row[field] for field in MASTER_FIELDS})
        if issues:
            exception_rows.append({field: silver_row[field] for field in MASTER_FIELDS})
            for issue in issues:
                issue_row = {
                    "document_id": normalized["document_id"],
                    "document_type": normalized["document_type"],
                    "source_file": normalized["source_file"],
                    "field_name": issue["field_name"],
                    "issue_type": issue["issue_type"],
                    "issue_detail": issue["issue_detail"],
                }
                issue_rows.append(issue_row)
                conn.execute(
                    "INSERT INTO validation_issues VALUES (?, ?, ?, ?, ?, ?)",
                    tuple(issue_row[field] for field in ISSUE_FIELDS),
                )
    conn.commit()
    approved = [row for row in master_rows if row["document_id"] not in {item["document_id"] for item in exception_rows}]
    return approved, exception_rows, issue_rows


def write_architecture_flow(output_path: Path = ARCHITECTURE_FLOW_PATH) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="620" viewBox="0 0 1400 620">
  <defs>
    <linearGradient id="hero" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#0c2746"/>
      <stop offset="100%" stop-color="#1667aa"/>
    </linearGradient>
    <linearGradient id="arrow" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0%" stop-color="#0f766e"/>
      <stop offset="100%" stop-color="#1263a3"/>
    </linearGradient>
    <style>
      .title { font: 800 34px 'Segoe UI', Arial, sans-serif; fill: white; }
      .subtitle { font: 400 17px 'Segoe UI', Arial, sans-serif; fill: #ddeeff; }
      .stepTitle { font: 800 20px 'Segoe UI', Arial, sans-serif; fill: #132238; }
      .stepBody { font: 500 15px 'Segoe UI', Arial, sans-serif; fill: #627182; }
      .mini { font: 700 12px 'Segoe UI', Arial, sans-serif; fill: #1263a3; letter-spacing: 1px; text-transform: uppercase; }
      .artifact { font: 700 15px 'Segoe UI', Arial, sans-serif; fill: #0f766e; }
    </style>
  </defs>
  <rect width="1400" height="620" fill="#edf4f8"/>
  <rect x="36" y="28" width="1328" height="108" rx="26" fill="url(#hero)"/>
  <text x="68" y="76" class="title">Document AI Ops Intake - Workflow</text>
  <text x="68" y="108" class="subtitle">From messy operational files to validated spreadsheet outputs and exception handling</text>

  <rect x="50" y="186" width="260" height="250" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="74" y="220" class="mini">Inputs</text>
  <text x="74" y="254" class="stepTitle">Operational document inbox</text>
  <text x="74" y="286" class="stepBody">Work orders</text>
  <text x="74" y="316" class="stepBody">Technician reports</text>
  <text x="74" y="346" class="stepBody">Inspection checklist exports</text>
  <text x="74" y="376" class="stepBody">Vendor requests</text>
  <text x="74" y="406" class="stepBody">Parts request forms</text>

  <rect x="374" y="186" width="260" height="250" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="398" y="220" class="mini">Stage 1</text>
  <text x="398" y="254" class="stepTitle">Bronze registration</text>
  <text x="398" y="286" class="stepBody">Register source file metadata</text>
  <text x="398" y="316" class="stepBody">Preserve raw excerpts</text>
  <text x="398" y="346" class="stepBody">Track original document type</text>

  <rect x="698" y="186" width="260" height="250" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="722" y="220" class="mini">Stage 2</text>
  <text x="722" y="254" class="stepTitle">Extraction and normalization</text>
  <text x="722" y="286" class="stepBody">Capture operational fields</text>
  <text x="722" y="316" class="stepBody">Standardize priorities and categories</text>
  <text x="722" y="346" class="stepBody">Create routing and summary fields</text>

  <rect x="1022" y="186" width="300" height="250" rx="22" fill="white" stroke="#d8e2ed"/>
  <text x="1046" y="220" class="mini">Stage 3</text>
  <text x="1046" y="254" class="stepTitle">Validation and business outputs</text>
  <text x="1046" y="286" class="stepBody">Check required fields, dates, and values</text>
  <text x="1046" y="316" class="stepBody">Separate clean records from exceptions</text>
  <text x="1046" y="346" class="stepBody">Export CSV, XLSX, dashboard, and issue log</text>

  <rect x="846" y="474" width="476" height="100" rx="18" fill="#f6fbfa" stroke="#b7ddd5"/>
  <text x="870" y="508" class="mini">Outputs</text>
  <text x="870" y="538" class="artifact">master_operational_intake.xlsx | exceptions_queue.csv | validation_results.csv | dashboard.html</text>

  <rect x="698" y="474" width="120" height="100" rx="18" fill="#f8f9fc" stroke="#d8e2ed"/>
  <text x="722" y="508" class="mini">Control</text>
  <text x="722" y="538" class="stepBody">validation_issues</text>

  <line x1="310" y1="308" x2="374" y2="308" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="374,308 350,294 350,322" fill="#1263a3"/>
  <line x1="634" y1="308" x2="698" y2="308" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="698,308 674,294 674,322" fill="#1263a3"/>
  <line x1="958" y1="308" x2="1022" y2="308" stroke="url(#arrow)" stroke-width="8" stroke-linecap="round"/>
  <polygon points="1022,308 998,294 998,322" fill="#1263a3"/>
  <line x1="758" y1="436" x2="758" y2="474" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
  <line x1="1086" y1="436" x2="1086" y2="474" stroke="#0f766e" stroke-width="6" stroke-linecap="round"/>
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def render_dashboard(master_rows: list[dict[str, str]], exception_rows: list[dict[str, str]], issue_rows: list[dict[str, str]], output_path: Path = DASHBOARD_PATH) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    priority_counts = Counter(row["priority"] for row in master_rows)
    type_counts = Counter(row["document_type"] for row in master_rows + exception_rows)
    issue_counts = Counter(row["issue_type"] for row in issue_rows)
    total_docs = len(master_rows) + len(exception_rows)
    total_cost = sum(float(row["estimated_cost"]) for row in master_rows if row["estimated_cost"])
    route_counts = Counter(row["route_to_team"] for row in master_rows)
    max_type = max(type_counts.values() or [1])
    doc_type_chart = "".join(
        f"""
        <div class="viz-row">
          <span>{html.escape(name.replace('_', ' ').title())}</span>
          <div class="viz-track"><span style="width:{int((count / max_type) * 100)}%"></span></div>
          <strong>{count}</strong>
        </div>
        """
        for name, count in sorted(type_counts.items())
    )
    route_tiles = "".join(
        f"""
        <article class="route-tile">
          <span>{html.escape(name.replace('_', ' ').title())}</span>
          <strong>{count}</strong>
        </article>
        """
        for name, count in route_counts.most_common(4)
    )

    priority_cards = "".join(
        f"<article class='mini-card priority-{html.escape(priority)}'><div class='mini-label'>{html.escape(priority.title())}</div><div class='metric-sm'>{count}</div></article>"
        for priority, count in sorted(priority_counts.items())
    )
    issue_items = "".join(
        f"<li><strong>{html.escape(name)}</strong>: {count}</li>"
        for name, count in sorted(issue_counts.items(), key=lambda item: item[1], reverse=True)
    )
    row_items = "".join(
        f"""
        <tr>
          <td><strong>{html.escape(row['document_id'])}</strong><br><span>{html.escape(row['document_type'])}</span></td>
          <td>{html.escape(row['asset_id'])}</td>
          <td>{html.escape(row['site'])}</td>
          <td>{html.escape(row['priority'])}</td>
          <td>{html.escape(row['route_to_team'])}</td>
          <td>{html.escape(row['summary_for_business'])}</td>
        </tr>
        """
        for row in master_rows[:8]
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
      --ink: #1e2430;
      --muted: #6d7381;
      --line: #e4dfd6;
      --blue: #3467eb;
      --teal: #2aa889;
      --rose: #f97393;
      --gold: #f2b65a;
      --bg: #fff8ee;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI", Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(242, 182, 90, 0.16), transparent 24%),
        radial-gradient(circle at top right, rgba(249, 115, 147, 0.14), transparent 24%),
        var(--bg);
      color: var(--ink);
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px 18px 44px; }}
    .hero {{ background: linear-gradient(135deg, #fff4d8, #ffe2dc 45%, #f8d9f0); color: #3a2b2b; border-radius: 24px; padding: 30px; border: 1px solid rgba(171, 143, 114, 0.18); }}
    .hero p {{ color: #6c5550; max-width: 760px; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0; }}
    .card, .panel, .mini-card, .route-tile {{ background: rgba(255, 255, 255, 0.88); border: 1px solid var(--line); border-radius: 18px; box-shadow: 0 8px 24px rgba(70, 50, 30, 0.08); }}
    .card, .mini-card {{ padding: 18px; }}
    .label, .mini-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .metric {{ margin-top: 8px; font-size: 30px; font-weight: 800; }}
    .metric-sm {{ margin-top: 8px; font-size: 24px; font-weight: 800; }}
    .grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; }}
    .triple {{ display: grid; grid-template-columns: 1fr 1fr 0.9fr; gap: 16px; margin-bottom: 16px; }}
    .panel-content {{ padding: 18px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ font-size: 12px; text-transform: uppercase; color: var(--muted); background: #f5f8fb; }}
    td span {{ color: var(--muted); font-size: 13px; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .priority-critical {{ background: linear-gradient(135deg, #ffe0e6, #fff); }}
    .priority-high {{ background: linear-gradient(135deg, #ffeacc, #fff); }}
    .priority-medium {{ background: linear-gradient(135deg, #e6f2ff, #fff); }}
    .priority-low {{ background: linear-gradient(135deg, #e3faf1, #fff); }}
    .viz-row {{
      display: grid;
      grid-template-columns: 1fr 1fr auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
    }}
    .viz-track {{
      height: 10px;
      background: #f1e7dc;
      border-radius: 999px;
      overflow: hidden;
    }}
    .viz-track span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--gold), var(--rose));
    }}
    .route-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .route-tile {{
      padding: 16px;
    }}
    .route-tile span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .route-tile strong {{ font-size: 26px; }}
    @media (max-width: 920px) {{ .cards, .grid, .mini-grid, .triple, .route-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <h1>{PROJECT_TITLE}</h1>
        <p>Document processing workflow for operational teams, converting scattered requests, reports, and checklist exports into structured, reviewable, spreadsheet-ready data.</p>
  </section>

  <section class="cards">
    <article class="card"><div class="label">Documents processed</div><div class="metric">{total_docs}</div></article>
    <article class="card"><div class="label">Approved records</div><div class="metric">{len(master_rows)}</div></article>
    <article class="card"><div class="label">Exception queue</div><div class="metric">{len(exception_rows)}</div></article>
    <article class="card"><div class="label">Estimated tracked cost</div><div class="metric">${total_cost:,.0f}</div></article>
  </section>

  <section class="triple">
    <section class="panel">
      <div class="panel-content">
        <h2>Document mix</h2>
        <p>Shows which kinds of documents dominated the intake window.</p>
        {doc_type_chart}
      </div>
    </section>
    <section class="panel">
      <div class="panel-content">
        <h2>Routing map</h2>
        <p>Clean records are enriched with routing hints so teams can triage faster.</p>
        <div class="route-grid">{route_tiles}</div>
      </div>
    </section>
    <section class="panel">
      <div class="panel-content">
        <h2>Priority mix</h2>
        <div class="mini-grid">{priority_cards}</div>
      </div>
    </section>
  </section>

  <section class="grid">
    <section class="panel">
      <div class="panel-content">
        <h2>What the workflow does</h2>
        <p>Ingests operational documents, extracts key fields, applies business rules, routes incomplete items to review, and publishes clean records for downstream use.</p>
        <h2>Structured output preview</h2>
        <table>
          <thead>
            <tr><th>Document</th><th>Asset</th><th>Site</th><th>Priority</th><th>Route</th><th>Summary</th></tr>
          </thead>
          <tbody>{row_items}</tbody>
        </table>
      </div>
    </section>
    <section class="panel">
      <div class="panel-content">
        <h2>Document types</h2>
        <ul>
          {''.join(f"<li><strong>{html.escape(name)}</strong>: {count}</li>" for name, count in sorted(type_counts.items()))}
        </ul>
        <h2>Validation issues caught</h2>
        <ul>{issue_items}</ul>
        <p>This layer flags missing asset references, invalid priorities, negative values, and incomplete vendor requests before data reaches business users.</p>
      </div>
    </section>
  </section>
</main>
</body>
</html>
""",
        encoding="utf-8",
    )
    return output_path


def write_case_summary(master_rows: list[dict[str, str]], exception_rows: list[dict[str, str]], issue_rows: list[dict[str, str]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    top_categories = Counter(row["normalized_issue_category"] for row in master_rows)
    issue_counts = Counter(row["issue_type"] for row in issue_rows)
    CASE_SUMMARY_PATH.write_text(
        "\n".join(
            [
                f"# {PROJECT_TITLE}",
                "",
                "## Recruiter Summary",
                "",
                "Built a local document intake workflow that transformed synthetic maintenance and service records into validated operational datasets, spreadsheet exports, and a review dashboard for business users.",
                "",
                "## What the pipeline handled",
                "",
                f"- Approved records: {len(master_rows)}",
                f"- Exception queue: {len(exception_rows)}",
                "",
                "## Top normalized categories",
                "",
                *[f"- {name}: {count}" for name, count in top_categories.most_common()],
                "",
                "## Validation issues caught",
                "",
                *[f"- {name}: {count}" for name, count in issue_counts.most_common()],
                "",
                "## Stack",
                "",
                "Python, SQLite, CSV, XLSX export, HTML dashboard, semi-structured document extraction, validation rules.",
            ]
        ),
        encoding="utf-8",
    )
    return CASE_SUMMARY_PATH


def run_pipeline(regenerate_data: bool = True) -> dict[str, str]:
    if regenerate_data:
        generate_all()
    records = extract_documents(INBOX_DIR)
    conn = prepare_database()
    try:
        insert_bronze(conn, records)
        master_rows, exception_rows, issue_rows = build_silver(conn, records)
        write_csv(MASTER_CSV_PATH, master_rows, MASTER_FIELDS)
        write_simple_xlsx(MASTER_XLSX_PATH, master_rows, MASTER_FIELDS, "approved_records")
        write_csv(EXCEPTIONS_CSV_PATH, exception_rows, MASTER_FIELDS)
        write_simple_xlsx(EXCEPTIONS_XLSX_PATH, exception_rows, MASTER_FIELDS, "exceptions")
        write_csv(VALIDATION_CSV_PATH, issue_rows, ISSUE_FIELDS)
        write_architecture_flow()
        render_dashboard(master_rows, exception_rows, issue_rows)
        write_case_summary(master_rows, exception_rows, issue_rows)
    finally:
        conn.close()
    return {
        "database": str(DB_PATH),
        "master_csv": str(MASTER_CSV_PATH),
        "master_xlsx": str(MASTER_XLSX_PATH),
        "exceptions_csv": str(EXCEPTIONS_CSV_PATH),
        "architecture_flow": str(ARCHITECTURE_FLOW_PATH),
        "dashboard": str(DASHBOARD_PATH),
        "summary": str(CASE_SUMMARY_PATH),
    }


def main() -> int:
    outputs = run_pipeline(regenerate_data=True)
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
