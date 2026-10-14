# ADR 0004: Warehouse adapters behind one interface
**Decision:** `Adapter.query(sql)` with DuckDB (default, local), Snowflake and Databricks implementations. The vendor connectors are optional extras and are imported lazily. Tests inject mock `connect` functions, so CI never needs credentials.
