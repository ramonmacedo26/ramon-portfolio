# Industrial Data & AI Copilot - Predictive Maintenance Analytics

Portfolio case study by Ramon Macedo.

This project shows how I approach practical Data Engineering + AI Automation work in an industrial context: turn messy operational files into a reliable analytics layer, identify maintenance risk, and generate short work-order briefs for business users.

No employer or client data is included. The data is synthetic and intentionally includes dirty records so the quality layer has something realistic to catch.

## What this demonstrates

- Data pipeline design across Bronze, Silver, and Gold layers.
- Python + SQL data engineering with a local SQLite warehouse.
- Data quality checks for duplicates, missing values, invalid workflow states, and physically impossible sensor readings.
- Industrial analytics using sensor readings, maintenance orders, work reports, and cost events.
- AI-style automation: rule-based extraction of maintenance signals and concise work-order briefs.
- Recruiter-friendly output: a static dashboard and short case summary.

## Business problem

Industrial teams often have useful operational data spread across sensor logs, work orders, cost exports, and free-text reports. The friction is not only technical: the data needs to be validated, modeled, summarized, and translated into actions that maintenance and operations teams can actually use.

This demo simulates that workflow end to end.

## Architecture

```text
raw CSV files
  -> Bronze SQLite tables
  -> Silver validated tables + data quality issue log
  -> Gold equipment health summary + work-order copilot briefs
  -> dashboard.html + case_summary.md
```

## Quick start

From this folder:

```powershell
python .\scripts\run_pipeline.py
python -m unittest discover -s .\tests
```

Generated outputs:

- `data/raw/*.csv`: synthetic source files.
- `data/warehouse/industrial_ops.db`: local warehouse.
- `outputs/dashboard.html`: recruiter-friendly dashboard.
- `outputs/case_summary.md`: short written summary.

## Example outputs

![Dashboard preview](outputs/dashboard_preview.svg)

The dashboard highlights:

- highest-risk equipment;
- open work orders;
- anomaly counts;
- estimated maintenance cost exposure;
- data quality issues caught before analytics consumption;
- AI-style work-order briefs.

## Data model

Bronze tables preserve ingested source rows:

- `bronze_sensor_readings`
- `bronze_maintenance_orders`
- `bronze_cost_events`
- `bronze_work_reports`

Silver tables standardize and validate records:

- `silver_sensor_readings`
- `silver_maintenance_orders`
- `silver_cost_events`
- `silver_work_reports`
- `data_quality_issues`

Gold tables are analytics-ready:

- `gold_equipment_health_summary`
- `gold_work_order_copilot_briefs`

## Why this is relevant to Data Engineer + AI roles

This case connects the core pieces companies usually need from modern data engineers:

- reliable ingestion;
- quality gates;
- medallion-style modeling;
- SQL-ready warehouse outputs;
- domain-aware business metrics;
- readable documentation;
- automation that helps non-technical users act faster.

It also reflects my strongest professional positioning: Mechanical Engineering background, industrial/Oil & Gas exposure, and hands-on work with Python, SQL, PySpark, Microsoft Fabric, Power BI, and AI-assisted workflow automation.

## Next improvements

- Add a public deployment of the dashboard.
- Add a Power BI version of the Gold model.
- Add dbt-style tests or Great Expectations-style checks.
- Add an optional LLM layer for richer report summarization when API credentials are available.
- Add screenshots to the README after the dashboard is published.
