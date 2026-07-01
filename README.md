# Data Quality & Monitoring Framework

Reusable Python framework for automated data quality checks on PostgreSQL/Redshift tables — schema validation, null/duplicate detection, referential integrity, and statistical outlier alerting. Simulates production-grade data observability.

## What It Does

```
PostgreSQL / Redshift Table
         │
         ▼
  DQ Check Runner
  ├── Schema Validation    → column names, types, nullability
  ├── Null Check           → null % per column vs threshold
  ├── Duplicate Check      → duplicate row detection
  ├── Referential Check    → FK integrity across tables
  └── Statistical Check    → mean/stddev outlier detection
         │
         ▼
  Report Generator         → HTML + JSON report
         │
         ▼
  Alert Engine             → log / email / Slack alert on failure
```

## Tech Stack

| Component | Tool |
|-----------|------|
| Data Quality | Great Expectations |
| Data Manipulation | Pandas |
| Database | PostgreSQL / Redshift |
| Reporting | Jinja2 HTML reports |
| Testing | pytest |
| CI | GitHub Actions |

## Project Structure

```
data-quality-framework/
├── checks/
│   ├── schema_check.py         # Validate column names, types, nullability
│   ├── null_check.py           # Null percentage per column
│   ├── duplicate_check.py      # Detect duplicate rows
│   ├── referential_check.py    # FK integrity across tables
│   └── statistical_check.py   # Mean/stddev outlier detection
├── reports/
│   └── report_generator.py    # Generate HTML + JSON quality reports
├── runner.py                  # Main entry point — run all checks
├── config.yml                 # Table configs and thresholds
├── tests/
│   └── test_checks.py         # pytest unit tests
├── .github/workflows/
│   └── ci.yml
└── requirements.txt
```

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Configure tables to check in config.yml
# Run all checks
python runner.py --table raw.yellow_trips --connection $DB_CONN

# Output
# ✅ Schema check passed
# ✅ Null check passed (max null % = 2.3%)
# ⚠️  Duplicate check: 142 duplicate rows found
# ✅ Statistical check passed
# Report saved to reports/output/dq_report_2024-01-15.html
```

## Data Quality Rules

| Check | Rule | Threshold |
|-------|------|-----------|
| Null | % nulls per column | < 5% (configurable) |
| Duplicate | Exact duplicate rows | 0 |
| Schema | Column existence + type | Exact match |
| Statistical | Values within N stddev of mean | 3σ |

## Status

- [ ] Schema validation check
- [ ] Null/completeness check
- [ ] Duplicate detection check
- [ ] Statistical outlier check
- [ ] HTML report generator
- [ ] pytest unit tests
- [ ] GitHub Actions CI
