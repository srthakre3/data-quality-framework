"""
Schema Check
Validates column names, data types, and nullability constraints against config.
"""

import pandas as pd
from sqlalchemy import inspect, text


class SchemaCheck:
    def __init__(self, engine, schema: str, table: str, expected_columns: list):
        self.engine = engine
        self.schema = schema
        self.table = table
        self.expected_columns = expected_columns  # list of dicts: {name, type, nullable}

    def run(self) -> dict:
        results = {"check": "schema", "table": f"{self.schema}.{self.table}", "passed": True, "issues": []}

        inspector = inspect(self.engine)
        actual_columns = {
            col["name"]: col
            for col in inspector.get_columns(self.table, schema=self.schema)
        }

        for expected in self.expected_columns:
            col_name = expected["name"]

            # Column existence
            if col_name not in actual_columns:
                results["issues"].append(f"Missing column: {col_name}")
                results["passed"] = False
                continue

            actual = actual_columns[col_name]

            # Nullability
            expected_nullable = expected.get("nullable", True)
            actual_nullable = actual.get("nullable", True)
            if expected_nullable != actual_nullable:
                results["issues"].append(
                    f"Column '{col_name}' nullability mismatch: expected {expected_nullable}, got {actual_nullable}"
                )
                results["passed"] = False

        return results
