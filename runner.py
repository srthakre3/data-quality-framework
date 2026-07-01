"""
Data Quality Framework — Main Runner
Usage:
    python runner.py --connection postgresql://user:pass@localhost:5432/mydb
    python runner.py --connection $DB_CONN --table raw.yellow_trips
"""

import argparse
import sys
import yaml
from sqlalchemy import create_engine

from checks.schema_check import SchemaCheck
from checks.null_check import NullCheck
from checks.duplicate_check import DuplicateCheck
from checks.referential_check import ReferentialCheck
from checks.statistical_check import StatisticalCheck
from reports.report_generator import generate_report


def load_config(path: str = "config.yml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_checks_for_table(engine, table_cfg: dict) -> list:
    schema = table_cfg["schema"]
    table = table_cfg["table"]
    primary_key = table_cfg.get("primary_key")
    checks_cfg = table_cfg.get("checks", {})
    columns = table_cfg.get("columns", [])
    ref_checks = table_cfg.get("referential_checks", [])

    results = []
    print(f"\n{'='*50}")
    print(f"Checking {schema}.{table}")
    print(f"{'='*50}")

    # Schema
    r = SchemaCheck(engine, schema, table, columns).run()
    _print_result(r)
    results.append(r)

    # Null
    r = NullCheck(engine, schema, table, checks_cfg.get("null_threshold_pct", 5.0)).run()
    _print_result(r)
    results.append(r)

    # Duplicate
    r = DuplicateCheck(engine, schema, table, primary_key).run()
    _print_result(r)
    results.append(r)

    # Referential
    r = ReferentialCheck(engine, schema, table, ref_checks).run()
    _print_result(r)
    results.append(r)

    # Statistical
    r = StatisticalCheck(engine, schema, table, checks_cfg.get("outlier_sigma", 3.0)).run()
    _print_result(r)
    results.append(r)

    return results


def _print_result(r: dict):
    icon = "✅" if r.get("passed", True) else "❌"
    print(f"  {icon} {r['check'].upper()} check: {'PASS' if r.get('passed', True) else 'FAIL'}")
    for issue in r.get("issues", []):
        print(f"      ⚠️  {issue}")


def main():
    parser = argparse.ArgumentParser(description="Run data quality checks")
    parser.add_argument("--connection", required=True, help="SQLAlchemy connection string")
    parser.add_argument("--table", default=None, help="schema.table to check (default: all in config)")
    parser.add_argument("--config", default="config.yml", help="Path to config.yml")
    args = parser.parse_args()

    config = load_config(args.config)
    engine = create_engine(args.connection)

    tables = config["tables"]
    if args.table:
        schema, table = args.table.split(".")
        tables = [t for t in tables if t["schema"] == schema and t["table"] == table]
        if not tables:
            print(f"ERROR: {args.table} not found in config.yml")
            sys.exit(1)

    all_results = []
    for table_cfg in tables:
        all_results.extend(run_checks_for_table(engine, table_cfg))

    generate_report(all_results)

    failed = [r for r in all_results if not r.get("passed", True)]
    if failed:
        print(f"\n❌ {len(failed)} check(s) failed.")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(all_results)} checks passed.")


if __name__ == "__main__":
    main()
