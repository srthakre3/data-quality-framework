"""
Referential Integrity Check
Verifies that FK column values in a table exist in the referenced dimension table.
"""

from sqlalchemy import text


class ReferentialCheck:
    def __init__(self, engine, schema: str, table: str, referential_checks: list):
        """
        referential_checks: list of dicts, each with keys:
            column, ref_schema, ref_table, ref_column
        """
        self.engine = engine
        self.schema = schema
        self.table = table
        self.referential_checks = referential_checks

    def run(self) -> dict:
        results = {
            "check": "referential",
            "table": f"{self.schema}.{self.table}",
            "passed": True,
            "issues": [],
            "details": {},
        }

        if not self.referential_checks:
            results["details"]["skipped"] = True
            return results

        with self.engine.connect() as conn:
            for fk in self.referential_checks:
                col = fk["column"]
                ref_schema = fk["ref_schema"]
                ref_table = fk["ref_table"]
                ref_col = fk["ref_column"]

                orphan_sql = text(f"""
                    SELECT COUNT(*) AS orphan_count
                    FROM "{self.schema}"."{self.table}" t
                    LEFT JOIN "{ref_schema}"."{ref_table}" r
                      ON t."{col}" = r."{ref_col}"
                    WHERE r."{ref_col}" IS NULL
                      AND t."{col}" IS NOT NULL
                """)
                orphan_count = conn.execute(orphan_sql).scalar()
                key = f"{col} -> {ref_schema}.{ref_table}.{ref_col}"
                results["details"][key] = orphan_count

                if orphan_count > 0:
                    results["issues"].append(
                        f"{orphan_count} orphan rows: '{col}' not found in {ref_schema}.{ref_table}.{ref_col}"
                    )
                    results["passed"] = False

        return results
