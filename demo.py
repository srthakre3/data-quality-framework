"""
demo.py — Data Quality Framework Demo
======================================
Generates realistic NYC taxi trip data, intentionally injects data quality
issues, then runs all checks and opens the HTML report in your browser.

Run:
    python demo.py
"""

import os
import random
import webbrowser
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import create_engine, text

from checks.null_check import NullCheck
from checks.duplicate_check import DuplicateCheck
from checks.schema_check import SchemaCheck
from checks.referential_check import ReferentialCheck
from checks.statistical_check import StatisticalCheck
from reports.report_generator import generate_report

# ── Config ────────────────────────────────────────────────────────────────────
SCHEMA = "main"       # SQLite doesn't use schemas; we'll alias as "main"
TABLE  = "yellow_trips"
PK     = "trip_id"
N_ROWS = 500
random.seed(42)

# ── Helpers ───────────────────────────────────────────────────────────────────

def random_datetime(start_year=2024):
    base = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    return base + timedelta(seconds=random.randint(0, 365 * 24 * 3600))


def generate_trips(n: int) -> pd.DataFrame:
    """Generate realistic NYC taxi data with injected DQ issues."""
    rows = []
    for i in range(1, n + 1):
        pickup  = random_datetime()
        dropoff = pickup + timedelta(minutes=random.randint(3, 60))
        fare    = round(random.uniform(5, 60), 2)

        rows.append({
            "trip_id":           f"T{i:05d}",
            "pickup_datetime":   pickup.strftime("%Y-%m-%d %H:%M:%S"),
            "dropoff_datetime":  dropoff.strftime("%Y-%m-%d %H:%M:%S"),
            "passenger_count":   random.choice([1, 1, 1, 2, 3, None]),   # ~16% null
            "trip_distance":     round(random.uniform(0.5, 20.0), 2),
            "fare_amount":       fare,
            "tip_amount":        round(random.uniform(0, fare * 0.3), 2) if random.random() > 0.1 else None,
            "total_amount":      round(fare * random.uniform(1.1, 1.4), 2),
        })

    df = pd.DataFrame(rows)

    # ── Inject issues ──────────────────────────────────────────────────────────
    # 1. Duplicate rows (exact)
    dupes = df.sample(5, random_state=1)
    df = pd.concat([df, dupes], ignore_index=True)
    print(f"  💉 Injected 5 duplicate rows")

    # 2. Statistical outlier — absurdly high fare
    df.loc[0, "fare_amount"] = 9999.99
    df.loc[1, "fare_amount"] = -50.00
    print(f"  💉 Injected 2 fare_amount outliers (9999.99 and -50.00)")

    return df


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*55)
    print("  Data Quality Framework — Live Demo")
    print("="*55)

    # 1. Build SQLite in-memory database
    engine = create_engine("sqlite:///:memory:")
    df = generate_trips(N_ROWS)

    with engine.begin() as conn:
        df.to_sql(TABLE, conn, index=False, if_exists="replace")
    print(f"\n✅ Loaded {len(df)} rows into in-memory SQLite ({TABLE})\n")

    # 2. Define expected schema (matches config.yml)
    expected_columns = [
        {"name": "trip_id",          "nullable": False},
        {"name": "pickup_datetime",  "nullable": False},
        {"name": "dropoff_datetime", "nullable": False},
        {"name": "passenger_count",  "nullable": True},
        {"name": "trip_distance",    "nullable": False},
        {"name": "fare_amount",      "nullable": False},
        {"name": "tip_amount",       "nullable": True},
        {"name": "total_amount",     "nullable": False},
    ]

    # SQLite uses "main" as its default schema
    schema = "main"

    # 3. Run all checks
    print("="*55)
    print(f"  Running checks on {schema}.{TABLE}")
    print("="*55)

    all_results = []

    checks = [
        ("Schema",      SchemaCheck(engine, schema, TABLE, expected_columns)),
        ("Null",        NullCheck(engine, schema, TABLE, threshold_pct=5.0)),
        ("Duplicate",   DuplicateCheck(engine, schema, TABLE, primary_key=PK)),
        ("Referential", ReferentialCheck(engine, schema, TABLE, referential_checks=[])),
        ("Statistical", StatisticalCheck(engine, schema, TABLE, sigma=3.0)),
    ]

    for name, check in checks:
        result = check.run()
        icon = "✅" if result.get("passed", True) else "❌"
        status = "PASS" if result.get("passed", True) else "FAIL"
        print(f"\n  {icon} {name.upper()} CHECK: {status}")
        for issue in result.get("issues", []):
            print(f"      ⚠️  {issue}")
        all_results.append(result)

    # 4. Generate report
    print("\n" + "="*55)
    paths = generate_report(all_results, output_dir="reports/output")

    # 5. Summary
    failed = [r for r in all_results if not r.get("passed", True)]
    passed = len(all_results) - len(failed)
    print(f"\n  {passed} checks passed  |  {len(failed)} checks failed")
    print("="*55)

    # 6. Open HTML report in browser
    html_abs = os.path.abspath(paths["html"])
    print(f"\n🌐 Opening report: {html_abs}")
    webbrowser.open(f"file://{html_abs}")


if __name__ == "__main__":
    main()
