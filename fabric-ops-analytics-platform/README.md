# Fabric Ops Analytics Platform

Portfolio case study by Ramon Macedo.

This project simulates the kind of operations analytics platform I would build for a Microsoft Fabric style environment: ingest messy source files, standardize them across Bronze/Silver/Gold layers, compute service and backlog KPIs, and publish a recruiter-friendly operations scorecard.

The goal is not to mimic the full Fabric UI locally. The goal is to show the architecture thinking, data modeling, validation, and business translation that a strong Fabric / Analytics Engineering project should demonstrate.

## Objective

Build a compact but believable operations analytics case that answers a simple question:

How do we turn disconnected service and maintenance extracts into a reliable decision layer for operations leaders?

This project is meant to prove that I can:

- structure a lakehouse-style analytics flow;
- validate messy operational records before business use;
- define useful Gold KPIs instead of only moving data around;
- communicate the result in a way that a hiring manager can understand quickly.

## What this project demonstrates

- Medallion-style data modeling across Bronze, Silver, and Gold.
- Operations analytics for service backlog, SLA risk, technician utilization, and downtime.
- Python orchestration with SQL-based warehouse transformations.
- Data quality checks for missing dimensions, invalid statuses, impossible durations, and malformed priorities.
- Business-facing outputs for operations leadership and service managers.
- Clear alignment with Microsoft Fabric, OneLake, Lakehouse, SQL, and analytics engineering roles.

## Business problem

Field service and maintenance teams often operate across spreadsheets, ticket exports, technician logs, and downtime reports. Even when the data exists, leaders still struggle to answer practical questions quickly:

- Which sites are missing SLA targets?
- Where is backlog building fastest?
- Which teams are overloaded?
- Which downtime drivers are costing the most?

This project simulates an internal analytics platform that turns those disconnected files into an operations scorecard.

## Architecture

```text
raw CSV extracts
  -> Bronze ingestion tables
  -> Silver validated and standardized tables
  -> Gold SLA, backlog, site, and workforce summaries
  -> dashboard.html + case_summary.md
```

## Flowchart

The visual flowchart is generated here:

- `outputs/architecture_flow.svg`

Flow summary:

```text
service_tickets.csv
technician_shifts.csv
downtime_events.csv
cost_ledger.csv
  -> Bronze raw tables
  -> Silver quality and standardization
  -> Gold business summaries and KPIs
  -> dashboard.html / case_summary.md
```

Detailed architecture notes live in:

- `docs/architecture_and_analysis.md`

## Fabric mapping

This is a local demo, but the architecture maps naturally to a Fabric-style setup:

- `data/raw/` -> landing zone / Bronze ingestion
- SQLite warehouse tables -> Lakehouse / Warehouse analytical layer
- Silver models -> cleaned, governed business-ready entities
- Gold models -> semantic-ready operational KPIs
- `outputs/dashboard.html` -> stakeholder-facing reporting layer

## Quick start

From this folder:

```powershell
python .\scripts\run_pipeline.py
python -m unittest discover -s .\tests
```

Generated outputs:

- `data/raw/*.csv`: synthetic source extracts
- `data/warehouse/fabric_ops.db`: local analytical warehouse
- `outputs/dashboard.html`: leadership scorecard
- `outputs/case_summary.md`: recruiter summary

## Folder structure

```text
fabric-ops-analytics-platform/
  data/
    raw/
      service_tickets.csv
      technician_shifts.csv
      downtime_events.csv
      cost_ledger.csv
    warehouse/
      fabric_ops.db
  docs/
    case_study.md
    architecture_and_analysis.md
  outputs/
    dashboard.html
    case_summary.md
  scripts/
    run_pipeline.py
  src/
    fabric_ops_platform/
      config.py
      generate_data.py
      pipeline.py
  tests/
    test_pipeline.py
```

## Dataset domains

The demo uses four operational source domains:

- service tickets
- technician shifts
- downtime events
- cost ledger

## Gold models

- `gold_site_operations_summary`
- `gold_technician_capacity_summary`
- `gold_priority_backlog_summary`
- `gold_exec_kpis`

## How to analyze the results

Use the outputs in this order:

1. Open `outputs/dashboard.html` for the business-facing view.
2. Read `outputs/case_summary.md` for a fast recruiter summary.
3. Inspect `gold_exec_kpis` to understand the topline numbers.
4. Inspect `gold_site_operations_summary` to see where risk is concentrated.
5. Inspect `gold_priority_backlog_summary` to understand which priorities drive the backlog.
6. Inspect `gold_technician_capacity_summary` to see workforce load and overtime.
7. Inspect `data_quality_issues` to verify which raw records were intentionally rejected or flagged.

Questions this project is designed to answer:

- Which sites are carrying the heaviest operational risk?
- How much open backlog and SLA pressure exists across the network?
- Are technician teams operating near capacity?
- How much downtime and cost exposure is accumulating?
- Did the pipeline catch bad source records before they contaminated executive metrics?

## How to visualize the results

The main visualization is `outputs/dashboard.html`. It is organized into four reading layers:

1. KPI cards
   These show the global topline: open backlog, breached SLAs, downtime hours, and average technician utilization.
2. Site operations summary
   This compares sites side by side on backlog, SLA pressure, workforce load, downtime, cost, and a synthetic risk score.
3. Top technician workload signals
   This helps identify overloaded or high-overtime workforce pockets.
4. Backlog and data quality
   This shows backlog by priority and confirms that the quality layer is active.

## Why this is a strong portfolio project

This project makes the Microsoft Fabric positioning much more explicit than a generic data pipeline demo. It shows platform thinking, KPI design, medallion structure, business context, and the ability to translate raw operations data into decisions.

It also pairs well with the existing industrial analytics case:

- `industrial-data-ai-copilot` shows industrial data and AI-style workflow support
- `fabric-ops-analytics-platform` shows operations platform design and analytics engineering

## Next improvements

- Add a Power BI mock layout or screenshot
- Add incremental refresh logic
- Add dbt-style test documentation
- Add a Fabric-specific architecture diagram
