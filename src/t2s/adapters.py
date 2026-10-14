"""Warehouse adapters. DuckDB is the default; Snowflake/Databricks are optional and lazily imported."""
from __future__ import annotations

import os
from typing import Any, Protocol


class Adapter(Protocol):
    dialect: str

    def query(self, sql: str) -> list[tuple[Any, ...]]: ...


class DuckDBAdapter:
    dialect = "duckdb"

    def __init__(self, con: Any = None) -> None:
        if con is None:
            from .data import build_db
            con = build_db()
        self.con = con

    def query(self, sql: str) -> list[tuple[Any, ...]]:
        return self.con.execute(sql).fetchall()


class SnowflakeAdapter:
    """Uses a read-only role. Credentials come from env vars, never from code."""
    dialect = "snowflake"

    def __init__(self, connect: Any = None) -> None:
        if connect is None:
            import snowflake.connector as sf
            connect = sf.connect
        self.con = connect(account=os.getenv("SNOWFLAKE_ACCOUNT"), user=os.getenv("SNOWFLAKE_USER"),
                           password=os.getenv("SNOWFLAKE_PASSWORD"), role=os.getenv("SNOWFLAKE_ROLE", "ANALYST_RO"),
                           warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"), database=os.getenv("SNOWFLAKE_DATABASE"),
                           schema=os.getenv("SNOWFLAKE_SCHEMA"))

    def query(self, sql: str) -> list[tuple[Any, ...]]:
        cur = self.con.cursor()
        try:
            cur.execute("ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 60")
            cur.execute(sql)
            return list(cur.fetchall())
        finally:
            cur.close()


class DatabricksAdapter:
    dialect = "databricks"

    def __init__(self, connect: Any = None) -> None:
        if connect is None:
            from databricks import sql as dbsql
            connect = dbsql.connect
        self.con = connect(server_hostname=os.getenv("DATABRICKS_HOST"), http_path=os.getenv("DATABRICKS_HTTP_PATH"),
                           access_token=os.getenv("DATABRICKS_TOKEN"))

    def query(self, sql: str) -> list[tuple[Any, ...]]:
        with self.con.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())
