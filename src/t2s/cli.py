from __future__ import annotations

import argparse

from . import bench
from .agent import Agent


def main() -> None:
    p = argparse.ArgumentParser("t2s")
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("ask")
    a.add_argument("question")
    s.add_parser("bench")
    args = p.parse_args()
    if args.cmd == "ask":
        r = Agent().ask(args.question)
        print(r.sql)
        for row in r.rows[:20]:
            print(row)
        if r.error:
            print("ERROR:", r.error)
        return
    r = bench.run()
    print("| question | correct | attempts |\n|---|---|---|")
    for q, ok, n in r["details"]:
        print(f"| {q} | {'yes' if ok else 'no'} | {n} |")
    print(f"\nexecution_accuracy={r['execution_accuracy']:.2f} ({r['n_questions']} q)  "
          f"guardrail_block_rate={r['guardrail_block_rate']:.2f} ({r['n_attacks']} attacks)  avg_latency_ms={r['avg_latency_ms']:.1f}")


if __name__ == "__main__":
    main()
