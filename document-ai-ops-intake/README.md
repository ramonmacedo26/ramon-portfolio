# Document AI Ops Intake

Portfolio case study by Ramon Macedo.

This project simulates a document-heavy operational workflow where requests, reports, checklists, and parts forms arrive in different formats and need to be turned into clean, traceable data before anyone can report on them or act on them.

Instead of treating document processing as a generic OCR demo, this case frames it as an operations problem: consolidate fragmented inputs, standardize the data, catch bad records early, and publish a usable spreadsheet for downstream teams.

No employer or client data is included. Every source file is synthetic and purposely includes incomplete fields, awkward wording, and invalid values so the control layer has realistic exceptions to catch.

## What this case proves

- I can design a practical intake workflow for semi-structured business documents.
- I can extract operational fields from mixed text and tabular inputs.
- I can apply data quality checks before the output reaches business users.
- I can separate approved records from items that need review.
- I can package the result in formats people actually use: CSV, XLSX, SQLite, and a lightweight dashboard.

## Business context

Many operations teams still receive maintenance requests, technician notes, inspection results, vendor updates, and parts demands through scattered files. The work is repetitive, the structure is inconsistent, and important details are easy to miss.

The point of this project is to show how that intake can be standardized into a repeatable workflow:

- collect incoming documents;
- capture the fields that matter;
- validate the results;
- route exceptions for review;
- publish a trusted structured dataset.

## Workflow overview

![Architecture flow](outputs/architecture_flow.svg)

Pipeline stages:

1. Generate a synthetic inbox with operational documents across five document groups.
2. Register each file in a Bronze-style intake layer with source metadata and raw text excerpts.
3. Extract key fields such as asset, site, priority, status, issue category, cost, and downtime.
4. Normalize labels and assign routing fields such as `route_to_team`, `urgency_flag`, and `severity_score`.
5. Validate required fields, dates, and numeric values.
6. Split the result into approved records and an exception queue.
7. Export spreadsheet-ready outputs plus a dashboard and validation log.

## Inputs

The generated inbox includes five realistic document groups:

- maintenance work orders in `.txt`
- technician service reports in `.md`
- inspection checklist exports in `.csv`
- vendor request messages in `.txt`
- spare-parts request exports in `.csv`

These files are intentionally mixed because real intake workflows are rarely clean or uniform.

## Outputs

Running the pipeline produces:

- `data/warehouse/document_ai_ops.db`: local SQLite warehouse
- `outputs/master_operational_intake.csv`: approved structured records
- `outputs/master_operational_intake.xlsx`: spreadsheet output for business users
- `outputs/exceptions_queue.csv`: records that need manual review
- `outputs/exceptions_queue.xlsx`: spreadsheet version of the exception queue
- `outputs/validation_results.csv`: detailed issue log
- `outputs/dashboard.html`: local dashboard for quick review
- `outputs/case_summary.md`: recruiter-facing summary

## Why the validation layer matters

The strongest part of the case is not just extraction. It is control.

The pipeline flags issues such as:

- missing asset references
- invalid priorities
- negative quantities or costs
- malformed dates
- incomplete vendor requests

That makes the output more believable because the workflow does not pretend every input is clean.

## How to run it

From this folder:

```powershell
& 'C:\Users\Windows 10\AppData\Local\Programs\Python\Python312\python.exe' .\scripts\run_pipeline.py
& 'C:\Users\Windows 10\AppData\Local\Programs\Python\Python312\python.exe' -m unittest discover -s .\tests
```

## Why this belongs in the portfolio

This case helps tell a clearer `Data + AI + Automation` story because it is easy to explain in business terms:

- documents come in messy;
- the workflow structures them;
- quality checks protect the output;
- stakeholders receive something they can use immediately.

That is much closer to real enterprise work than a generic chatbot or a one-off notebook.
