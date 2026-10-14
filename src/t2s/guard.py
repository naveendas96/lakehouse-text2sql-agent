"""SQL guardrails: read-only single SELECT, table/column allowlist, enforced row limit."""
from __future__ import annotations

import sqlglot
from sqlglot import exp


class SQLRejected(ValueError):
    pass


def validate(sql: str, allow: dict[str, set[str]], max_rows: int = 1000, dialect: str = "duckdb") -> str:
    try:
        stmts = sqlglot.parse(sql, read=dialect)
    except sqlglot.errors.ParseError as e:
        raise SQLRejected(f"parse error: {e}") from e
    if len(stmts) != 1 or stmts[0] is None:
        raise SQLRejected("exactly one statement allowed")
    tree = stmts[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        raise SQLRejected(f"only SELECT allowed, got {tree.key.upper()}")
    for bad in (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command):
        if tree.find(bad):
            raise SQLRejected(f"forbidden operation {bad.__name__}")
    ctes = {c.alias_or_name for c in tree.find_all(exp.CTE)}
    tables = {t.name for t in tree.find_all(exp.Table)} - ctes
    if bad_t := tables - allow.keys():
        raise SQLRejected(f"table not allowed: {sorted(bad_t)}")
    all_cols = set().union(*(allow[t] for t in tables)) if tables else set()
    aliases = {a.alias for a in tree.find_all(exp.Alias)}
    for c in tree.find_all(exp.Column):
        if c.name not in all_cols and c.name not in aliases and c.name != "*":
            raise SQLRejected(f"column not allowed: {c.name}")
    lim = tree.args.get("limit")
    if lim is None or int(lim.expression.name) > max_rows:
        tree = tree.limit(max_rows)
    return tree.sql(dialect=dialect)
