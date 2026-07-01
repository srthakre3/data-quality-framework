"""
Null Check
Computes null percentage per column and flags any that exceed the configured threshold.
"""

import pandas as pd
from sqlalchemy import text


class NullCheck:
    def __init__(self, engine, schema: str, table: str, threshold_pct: float = 5.0):
        self.engine = engine
        self.schema = schema
        self.table = table
        self.threshold_pct = threshold_pct

    def run(self) -> dict:
        results = {
            "check": "null",
            "table": f"{self.schema}.{self.table}",
            "passed": True,
            "issues": [],
            "details": {},
        }

        with self.engine.connect() as conn:
            df = pd.read_sql(
                text(f'SELECT * FROM "{self.schema}"."{self.table}" LIMIT 100000'),
                conn,
            )

        total_rows = len(df)
        if total_rows == 0:
            results["issues"].append("Table is empty")
            results["passed"] = False
            return results

        for col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / total_rows) * 100
            results["details"][col] = round(null_pct, 2)

            if null_pct > self.threshold_pct:
                results["issues"].append(
                    f"Column '{col}': {null_pct:.1f}% nulls (threshold: {self.threshold_pct}%)"
                )
                results["passed"] = False

        return results
