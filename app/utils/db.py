"""
db.py — DuckDB connection helper.

Connects read-only to the dbt-built warehouse at
dbt_project/warehouse.duckdb (relative to project root).
"""

import os
import duckdb
import pandas as pd

# Project root = two levels up from this file (app/utils/db.py)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WAREHOUSE_PATH = os.path.join(_PROJECT_ROOT, "dbt_project", "warehouse.duckdb")


def run_query(sql: str) -> pd.DataFrame:
    """
    Open a short-lived read-only connection, execute SQL, close immediately.
    Not cached — keeps the file lock free so MetricFlow CLI can open it too.
    """
    if not os.path.exists(WAREHOUSE_PATH):
        raise FileNotFoundError(
            f"Warehouse not found at {WAREHOUSE_PATH}. "
            "Run `dbt seed && dbt run` inside dbt_project/ first."
        )
    conn = duckdb.connect(WAREHOUSE_PATH, read_only=True)
    try:
        return conn.execute(sql).df()
    finally:
        conn.close()
