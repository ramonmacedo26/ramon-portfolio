# Fabric Ops Analytics Platform

Operations analytics portfolio case inspired by Microsoft Fabric, lakehouse thinking, and analytics engineering patterns for service and maintenance environments.

## Overview

This project simulates a multi-site operations analytics platform where disconnected service extracts are turned into a structured reporting layer. The pipeline ingests raw operational files, validates them through Bronze and Silver layers, models Gold KPIs, and publishes a leadership-ready scorecard.

The purpose is not to clone Microsoft Fabric locally. It is to show the architecture thinking, KPI design, validation logic, and business translation expected in Fabric-aligned data and analytics roles.

## Business Problem

Operations leaders often have data, but not a reliable decision layer. Service tickets, downtime logs, technician shifts, and cost records usually live in separate files or systems, which makes it harder to answer basic questions quickly:

- where is backlog building fastest
- which sites are under SLA pressure
- where is capacity stretched
- how much downtime and cost exposure is accumulating

This case turns those fragmented inputs into an operations scorecard designed for business use.

## What This Project Demonstrates

- medallion-style modeling across Bronze, Silver, and Gold
- KPI design for backlog, SLA risk, downtime, workforce load, and cost visibility
- Python orchestration with SQL-based transformations
- validation for malformed priorities, invalid statuses, impossible durations, and bad dimensional data
- executive-style dashboard output
- portfolio-safe Fabric positioning without depending on a live cloud environment

## Architecture

```text
raw CSV extracts
  -> Bronze ingestion tables
  -> Silver validation and standardization
  -> Gold site, backlog, workforce, and KPI summaries
  -> dashboard.html + case summary + case study
```

## Source Domains

The case uses four source domains:

- service tickets
- technician shifts
- downtime events
- cost ledger

These files are synthetic and intentionally include quality issues so the control layer has realistic edge cases to handle.

## Fabric Mapping

Even though this is a local demo, the structure maps naturally to a Fabric-style setup:

- `data/raw/` -> landing zone / Bronze ingestion
- warehouse tables -> analytical storage layer
- Silver models -> cleaned and standardized business entities
- Gold models -> semantic-ready KPI outputs
- `outputs/dashboard.html` -> stakeholder-facing reporting layer

## Outputs

Running the pipeline generates:

- `data/warehouse/fabric_ops.db` - local analytical warehouse
- `outputs/dashboard.html` - operations scorecard
- `outputs/case_summary.html` - short summary page
- `docs/case_study.html` - full case narrative
- `outputs/architecture_flow.svg` - visual pipeline flow

## Gold Models

- `gold_site_operations_summary`
- `gold_technician_capacity_summary`
- `gold_priority_backlog_summary`
- `gold_exec_kpis`

## Repository Structure

```text
fabric-ops-analytics-platform/
  docs/
    architecture_and_analysis.md
    case_study.html
    case_study.md
  outputs/
    architecture_flow.svg
    dashboard.html
    case_summary.html
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

## Quick Start

From this folder:

```powershell
python .\scripts\run_pipeline.py
python -m unittest discover -s .\tests
```

## How To Read The Output

The intended reading order is:

1. open `outputs/dashboard.html`
2. review the topline KPIs
3. compare site-level operations summaries
4. inspect workload and backlog concentration
5. verify which issues were intercepted by the quality layer

Questions this project is designed to answer:

- which sites are carrying the highest operational risk
- how much SLA pressure exists across the network
- whether teams are operating near capacity
- which drivers are increasing downtime and cost exposure

## Why This Case Matters

This project makes the analytics engineering and Fabric narrative much more concrete than a generic ETL demo. It shows:

- platform-style thinking
- business KPI modeling
- quality-aware transformation logic
- stakeholder-oriented delivery

Together with the other portfolio projects, it helps demonstrate a pattern: building practical decision layers on top of messy operational data.

