# Data Quality & Monitoring Framework

A production-style Python framework for automated data quality monitoring on PostgreSQL/Redshift tables. Runs configurable checks on any table, generates HTML + JSON reports, and integrates with CI/CD via GitHub Actions.

Built to demonstrate the kind of data observability tooling used in real analytics engineering workflows.

---
## Architecture

![Architecture Diagram](docs/architecture.svg)

The framework extracts raw tables from PostgreSQL, runs automated checks across three categories (schema validation, null/duplicate detection, statistical outlier alerting), outputs HTML and JSON reports, and enforces quality gates via pytest and GitHub Actions CI. All 6/6 tests pass.

## What It Does

```
PostgreSQL / Redshift Table
         │
         ▼
  DQ Check Runner
  ├── Schema Check       → column names, data types, nullability
  ├── Null Check         → null % per column vs configurable threshold
  ├── Duplicate Check    → PK duplicates + full-row duplicates
  ├── Referential Check  → FK integrity across tables (LEFT JOIN orphan scan)
  └── Statistical Check  → 3σ outlier detection on numeric columns
         │
         ▼
  Report Generator       → HTML dashboard + JSON output
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Database | PostgreSQL / Amazon Redshift |
| Data layer | pandas, SQLAlchemy |
| Reporting | Jinja2 HTML templates |
| Testing | pytest (SQLite in-memory fixtures) |
| CI | GitHub Actions |

---

## Project Structure

```
data-quality-framework/
├── checks/
│   ├── null_check.py           # Null % per column vs threshold
│   ├── duplicate_check.py      # PK + full-row duplicate detection
│   ├── schema_check.py         # Column existence, types, nullability
│   ├── referential_check.py    # FK integrity via LEFT JOIN orphan scan
│   └── statistical_check.py    # 3σ outlier detection on numeric columns
├── reports/
│   └── report_generator.py     # Renders HTML + JSON report from check results
├── tests/
│   └── test_checks.py          # 6 pytest unit tests with SQLite in-memory DB
├── runner.py                   # CLI entry point — runs all checks for configured tables
├── config.yml                  # Table definitions, thresholds, FK mappings
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions: syntax check + pytest on every push
└── requirements.txt
```

---

## Quickstart

```bash
git clone https://github.com/srthakre3/data-quality-framework.git
cd data-quality-framework
pip install -r requirements.txt

# Run unit tests (no database needed — uses SQLite in-memory)
python -m pytest tests/ -v

# Run the demo (no database needed — uses SQLite in-memory)
python demo.py

# Run against a real database
python runner.py --connection postgresql://user:pass@host:5432/db --table raw.yellow_trips
```

---

## Configuration

Tables and thresholds are defined in `config.yml`:

```yaml
tables:
  - schema: raw
    table: yellow_trips
    primary_key: trip_id
    checks:
      null_threshold_pct: 5.0   # fail if any column > 5% nulls
      outlier_sigma: 3.0        # flag values beyond 3 standard deviations
    columns:
      - { name: trip_id,        type: VARCHAR, nullable: false }
      - { name: fare_amount,    type: FLOAT,   nullable: false }
    referential_checks:
      - column: pickup_date
        ref_schema: marts
        ref_table: dim_date
        ref_column: date_id
```

---

## Sample Output

```
==================================================
Checking raw.yellow_trips
==================================================
  ✅ SCHEMA check: PASS
  ✅ NULL check: PASS
  ❌ DUPLICATE check: FAIL
      ⚠️  Primary key 'trip_id': 142 duplicate values found
  ✅ REFERENTIAL check: PASS
  ✅ STATISTICAL check: PASS

📄 Report saved: reports/output/dq_report_2025-01-15.html
📄 JSON saved:   reports/output/dq_report_2025-01-15.json

❌ 1 check(s) failed.
```

The HTML report renders a summary dashboard with pass/fail badges per check and a breakdown of all issues found.

---

## Checks Reference

| Check | What It Catches | Threshold |
|---|---|---|
| Schema | Missing columns, wrong types, nullability mismatches | Exact match |
| Null | Columns with too many missing values | Configurable % per table |
| Duplicate | Duplicate primary keys or identical rows | 0 duplicates |
| Referential | Orphan rows (FK values with no match in referenced table) | 0 orphans |
| Statistical | Numeric outliers beyond N standard deviations from mean | 3σ default |

---

## Tests

```
tests/test_checks.py::test_null_check_passes_under_threshold   PASSED
tests/test_checks.py::test_null_check_fails_over_threshold     PASSED
tests/test_checks.py::test_duplicate_check_clean               PASSED
tests/test_checks.py::test_duplicate_check_detects_dupes       PASSED
tests/test_checks.py::test_statistical_check_no_outliers       PASSED
tests/test_checks.py::test_report_generates_files              PASSED

6 passed in 0.40s
```

Tests use SQLite in-memory fixtures. No database setup required.

---

## CI

GitHub Actions runs on every push to `main`:
1. Syntax check all Python modules
2. Validate YAML config
3. Run full pytest suite

---

## Author

**Sanket Thakre**, Analytics Engineer / BIE @ Amazon  
[sanketthakre.me](https://sanketthakre.me) · [github.com/srthakre3](https://github.com/srthakre3)
