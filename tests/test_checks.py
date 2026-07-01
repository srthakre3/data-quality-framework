"""
Unit tests for DQ checks using an in-memory SQLite DB.
Run: pytest tests/ -v
"""

import pytest
import pandas as pd
from sqlalchemy import create_engine, text


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    """In-memory SQLite engine with test data."""
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("""
            CREATE TABLE yellow_trips (
                trip_id     TEXT NOT NULL,
                fare_amount REAL NOT NULL,
                tip_amount  REAL,
                trip_distance REAL NOT NULL
            )
        """))
        # Clean rows
        conn.execute(text("""
            INSERT INTO yellow_trips VALUES
              ('T001', 12.5, 2.0, 3.2),
              ('T002', 8.0,  1.5, 1.8),
              ('T003', 15.0, 0.0, 5.0),
              ('T004', 9.5,  NULL, 2.1),
              ('T005', 11.0, 1.0, 3.5)
        """))
    return eng


@pytest.fixture(scope="module")
def engine_with_dupes():
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("""
            CREATE TABLE dup_table (id TEXT, val REAL)
        """))
        conn.execute(text("""
            INSERT INTO dup_table VALUES ('A', 1.0), ('A', 1.0), ('B', 2.0)
        """))
    return eng


# ── Null Check Tests ──────────────────────────────────────────────────────────

def test_null_check_passes_under_threshold(engine):
    from checks.null_check import NullCheck
    # tip_amount has 1/5 = 20% nulls → threshold is 25% → should pass
    result = NullCheck(engine, "main", "yellow_trips", threshold_pct=25.0).run()
    assert result["passed"] is True
    assert result["details"]["tip_amount"] == 20.0


def test_null_check_fails_over_threshold(engine):
    from checks.null_check import NullCheck
    # threshold = 10% → tip_amount at 20% should fail
    result = NullCheck(engine, "main", "yellow_trips", threshold_pct=10.0).run()
    assert result["passed"] is False
    assert any("tip_amount" in issue for issue in result["issues"])


# ── Duplicate Check Tests ─────────────────────────────────────────────────────

def test_duplicate_check_clean(engine):
    from checks.duplicate_check import DuplicateCheck
    result = DuplicateCheck(engine, "main", "yellow_trips", primary_key="trip_id").run()
    assert result["passed"] is True
    assert result["details"]["duplicate_pk_count"] == 0
    assert result["details"]["exact_duplicate_rows"] == 0


def test_duplicate_check_detects_dupes(engine_with_dupes):
    from checks.duplicate_check import DuplicateCheck
    result = DuplicateCheck(engine_with_dupes, "main", "dup_table", primary_key="id").run()
    assert result["passed"] is False
    assert result["details"]["duplicate_pk_count"] >= 1


# ── Statistical Check Tests ───────────────────────────────────────────────────

def test_statistical_check_no_outliers(engine):
    from checks.statistical_check import StatisticalCheck
    # All fare_amounts are close together — no 3σ outliers expected
    result = StatisticalCheck(engine, "main", "yellow_trips", sigma=3.0).run()
    # With only 5 rows we skip (< 30), so issues should be empty
    assert result["issues"] == []


# ── Report Generator Tests ────────────────────────────────────────────────────

def test_report_generates_files(tmp_path):
    from reports.report_generator import generate_report
    dummy_results = [
        {"check": "null", "table": "raw.trips", "passed": True, "issues": []},
        {"check": "duplicate", "table": "raw.trips", "passed": False,
         "issues": ["5 duplicate rows found"]},
    ]
    paths = generate_report(dummy_results, output_dir=str(tmp_path))
    assert paths["html"].endswith(".html")
    assert paths["json"].endswith(".json")
    import os
    assert os.path.exists(paths["html"])
    assert os.path.exists(paths["json"])
