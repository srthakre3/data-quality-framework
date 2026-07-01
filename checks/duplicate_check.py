"""
Duplicate Check
Detects exact duplicate rows and duplicate primary key values.
"""

import pandas as pd
from sqlalchemy import text


class DuplicateCheck:
    def __init__(self, engine, schema: str, table: str, primary_key: str = None):
        self.engine = engine
        self.schema = schema
        self.table = table
        self.primary_key = primary_key

    def run(self) -> dict:
        results = {
            "check": "duplicate",
            "table": f"{self.schema}.{self.table}",
            "passed": True,
            "issues": [],
            "details": {},
        }

        with self.engine.connect() as conn:
            # Check PK uniqueness via SQL — faster than loading full table
            if self.primary_key:
                pk_dupe_sql = text(f"""
                    SELECT COUNT(*) AS total, COUNT(DISTINCT "{self.primary_key}") AS unique_pks
                    FROM "{self.schema}"."{self.table}"
                """)
                row = conn.execute(pk_dupe_sql).fetchone()
                total, unique_pks = row[0], row[1]
                pk_dupes = total - unique_pks
                results["details"]["total_rows"] = total
                results["details"]["unique_pk_values"] = unique_pks
                results["details"]["duplicate_pk_count"] = pk_dupes

                if pk_dupes > 0:
                    results["issues"].append(
                        f"Primary key '{self.primary_key}' has {pk_dupes} duplicate values"
                    )
                    results["passed"] = False

            # Full-row duplicate check (sample 100k rows)
            df = pd.read_sql(
                text(f'SELECT * FROM "{self.schema}"."{self.table}" LIMIT 100000'),
                conn,
            )

        full_dupes = df.duplicated().sum()
        results["details"]["exact_duplicate_rows"] = int(full_dupes)

        if full_dupes > 0:
            results["issues"].append(f"{full_dupes} exact duplicate rows found")
            results["passed"] = False

        return results
