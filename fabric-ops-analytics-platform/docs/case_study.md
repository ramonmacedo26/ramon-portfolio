# Case Study: Fabric Ops Analytics Platform

## Situation

Operations leaders receive fragmented exports from service systems, technician schedules, downtime logs, and cost trackers. Because the data is disconnected and inconsistent, backlog and SLA risk are difficult to monitor in time.

## Task

Build a compact but realistic analytics platform that ingests raw operational files, validates them, models Bronze/Silver/Gold layers, and produces a leadership-ready operations scorecard.

## Action

- Generated synthetic multi-site operations data with intentional quality issues.
- Loaded source extracts into Bronze tables without heavy assumptions.
- Standardized dimensions and business rules in Silver tables.
- Modeled Gold summaries for site performance, technician capacity, backlog by priority, and executive KPIs.
- Published a static HTML dashboard designed for a recruiter or hiring manager audience.

## Result

The final output makes it possible to spot SLA risk, backlog concentration, overloaded sites, and downtime cost exposure without manually reconciling source files.

## Stack

Python, SQL, SQLite, medallion architecture, operations analytics, data quality checks, HTML/CSS reporting.

