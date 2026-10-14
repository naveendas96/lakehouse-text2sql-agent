"""Text-to-SQL agent: semantic-layer prompt -> LLM -> guard -> execute -> self-correct on error."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .adapters import Adapter, DuckDBAdapter
from .guard import SQLRejected, validate
from .llm import LLM, get_llm

SEM = yaml.safe_load((Path(__file__).parent / "semantic.yaml").read_text())
ALLOW = {t: set(v["columns"]) for t, v in SEM["tables"].items()}


def _find(q: str, items: dict) -> list[str]:
    hits = []
    for name, v in items.items():
        for s in sorted(v["synonyms"], key=len, reverse=True):
            m = re.search(rf"\b{re.escape(s)}\b", q)
            if m:
                hits.append((m.start(), name))
                break
    return [n for _, n in sorted(hits)]


def semantic_compile(question: str) -> str:
    """Deterministic NL -> SQL via the semantic layer. Used as the mock LLM and as a grounding hint."""
    q = question.lower()
    metrics = _find(q, SEM["metrics"]) or ["revenue"]
    dims = [d for d in _find(q, SEM["dimensions"]) if not re.search(rf"\b(in|for) {d}\b", q)]
    tables, where = set(), []
    for f in SEM["filters"]:
        m = re.search(f["pattern"], q)
        if m:
            v = m.group(1).title() if f.get("title") else m.group(1)
            where.append(f["sql"].format(v))
            tables.add(f["table"])
    tables |= {SEM["dimensions"][d]["table"] for d in dims}
    sel = [f"{SEM['dimensions'][d]['sql']} AS {d}" for d in dims] + [f"{SEM['metrics'][m]['sql']} AS {m}" for m in metrics]
    sql = "SELECT " + ", ".join(sel) + " FROM fact_sales"
    for t in sorted(tables):
        sql += f" JOIN {t} ON {SEM['joins'][t]}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    if dims:
        sql += " GROUP BY " + ", ".join(str(i + 1) for i in range(len(dims)))
    m = re.search(r"top (\d+)", q)
    if dims:
        sql += f" ORDER BY {metrics[0]} DESC" if m or "highest" in q or "best" in q else " ORDER BY 1"
    if m:
        sql += f" LIMIT {m.group(1)}"
    return sql


def mock_handler(prompt: str, _s: str) -> str:
    q = prompt.split("QUESTION:")[-1].split("\n")[0].strip()
    return f"```sql\n{semantic_compile(q)}\n```"


SYSTEM = "You write DuckDB SQL. Use ONLY the tables, joins and metric definitions given. Return one SELECT in a ```sql block."


@dataclass
class Result:
    question: str
    sql: str | None
    rows: list[tuple[Any, ...]] = field(default_factory=list)
    attempts: int = 0
    error: str | None = None


class Agent:
    def __init__(self, adapter: Adapter | None = None, llm: LLM | None = None, max_attempts: int = 3) -> None:
        self.db = adapter or DuckDBAdapter()
        self.llm = llm or get_llm(mock_handler)
        self.max_attempts = max_attempts

    def prompt(self, q: str, feedback: str = "") -> str:
        ctx = yaml.safe_dump({k: SEM[k] for k in ("tables", "joins", "metrics")}, sort_keys=False)
        return f"SEMANTIC LAYER:\n{ctx}\nQUESTION: {q}\n" + (f"PREVIOUS ATTEMPT FAILED: {feedback}\nFix it.\n" if feedback else "")

    def ask(self, q: str) -> Result:
        fb, sql = "", None
        for i in range(1, self.max_attempts + 1):
            out = self.llm.complete(self.prompt(q, fb), SYSTEM)
            m = re.search(r"```sql\s*(.*?)```", out, re.S)
            raw = (m.group(1) if m else out).strip().rstrip(";")
            try:
                sql = validate(raw, ALLOW)
                return Result(q, sql, self.db.query(sql), i)
            except SQLRejected as e:
                fb = f"guardrail: {e}. SQL was: {raw}"
            except Exception as e:  # execution error -> self-correct
                fb = f"execution error: {e}. SQL was: {raw}"
        return Result(q, sql, [], self.max_attempts, fb)
