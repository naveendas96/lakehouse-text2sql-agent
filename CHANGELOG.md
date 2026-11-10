# Changelog

## Unreleased

- Added a "Run it in 60 seconds" section to the README (install + `t2s ask "top 5 stores by revenue"`). The documented command now uses `python3` rather than `python3.11`.
- Added GitHub issue and pull request templates.
- Extended the SQL guard tests to cover `UPDATE`, `COPY` and `CREATE`, and added a test that a user `LIMIT` below the cap is kept and that a CTE still gets a row cap.

## 0.1.0 - 2026-10-14

Initial public release: a governed text-to-SQL agent with a semantic layer, sqlglot allowlist guardrails, a bounded self-correction loop, a DuckDB star schema, and Snowflake/Databricks adapters. Defaults to a mock compiler.
