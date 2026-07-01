"""
Statistical Outlier Check
Flags numeric columns where values fall beyond N standard deviations from the mean.
"""

import pandas as pd
from sqlalchemy import text


class StatisticalCheck:
    def __init__(self, engine, schema: str, table: str, sigma: float = 3.0):
        self.engine = engine
        self.schema = schema
        self.table = table
        self.sigma = sigma

    def run(self) -> dict:
        results = {
            "check": "statistical",
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

        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 30:
                continue  # too few rows to be meaningful

            mean = series.mean()
            std = series.std()
            if std == 0:
                continue

            lower = mean - self.sigma * std
            upper = mean + self.sigma * std
            outlier_count = int(((series < lower) | (series > upper)).sum())

            results["details"][col] = {
                "mean": round(mean, 4),
                "std": round(std, 4),
                "lower_bound": round(lower, 4),
                "upper_bound": round(upper, 4),
                "outlier_count": outlier_count,
            }

            if outlier_count > 0:
                results["issues"].append(
                    f"Column '{col}': {outlier_count} outliers beyond {self.sigma}σ "
                    f"(range [{lower:.2f}, {upper:.2f}])"
                )
                results["passed"] = False

        return results
