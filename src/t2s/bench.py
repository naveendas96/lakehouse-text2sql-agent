"""Execution-accuracy benchmark + guardrail block rate."""
from __future__ import annotations

import time
from pathlib import Path

import yaml

from .agent import ALLOW, Agent
from .guard import SQLRejected, validate

DATA = Path(__file__).resolve().parents[2] / "data"


def _norm(rows: list[tuple]) -> list[tuple]:
    return sorted(tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows)


def run(agent: Agent | None = None) -> dict:
    agent = agent or Agent()
    cases = yaml.safe_load((DATA / "benchmark.yaml").read_text())
    ok, details, t0 = 0, [], time.perf_counter()
    for c in cases:
        r = agent.ask(c["q"])
        gold = agent.db.query(c["gold"])
        hit = r.error is None and _norm(r.rows) == _norm(gold)
        ok += hit
        details.append((c["q"], hit, r.attempts))
    blocked = 0
    attacks = yaml.safe_load((DATA / "guardrail_cases.yaml").read_text())
    for a in attacks:
        try:
            validate(a, ALLOW)
        except SQLRejected:
            blocked += 1
    return {"execution_accuracy": ok / len(cases), "n_questions": len(cases),
            "guardrail_block_rate": blocked / len(attacks), "n_attacks": len(attacks),
            "avg_latency_ms": (time.perf_counter() - t0) * 1000 / len(cases), "details": details}
