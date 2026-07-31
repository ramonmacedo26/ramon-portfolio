# Case Study: Industrial Data & AI Copilot

## Situation

Maintenance and operations teams receive sensor logs, work orders, cost events, and inspection reports in separate files. The result is slow prioritization, manual reconciliation, and unclear risk visibility.

## Task

Build a small but realistic data product that ingests raw operational files, validates them, creates analytics-ready tables, and produces clear maintenance recommendations.

## Action

- Generated synthetic industrial data with deliberate quality issues.
- Loaded raw files into Bronze tables.
- Built Silver tables with validation flags and a centralized quality log.
- Modeled Gold summaries for equipment health, cost exposure, open work orders, and risk scoring.
- Created AI-style work-order briefs from operational reports and maintenance context.
- Rendered a static dashboard for a non-technical stakeholder audience.

## Result

The final output makes it possible to identify high-risk equipment, see why each asset is risky, and act on open work orders without manually reading every source file.

## Stack

Python, SQL, SQLite, HTML/CSS, data quality checks, medallion architecture, operational analytics, AI-style summarization.
