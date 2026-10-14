# ADR 0002: AST-based SQL guardrails (sqlglot), not regex
**Decision:** Parse every generated statement. Reject anything that isn't exactly one SELECT or UNION, reject DML/DDL and commands (COPY and so on), enforce the table and column allowlist, and always inject or clamp `LIMIT 1000`.
**Defence in depth:** In production, also connect with a read-only role (`ANALYST_RO` in the Snowflake adapter) and set a statement timeout.
**Consequences:** Some valid-but-exotic SQL gets rejected. The agent then self-corrects.
