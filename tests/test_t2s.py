from unittest.mock import MagicMock

import pytest

from t2s.adapters import DatabricksAdapter, SnowflakeAdapter
from t2s.agent import ALLOW, Agent, semantic_compile
from t2s.bench import run
from t2s.guard import SQLRejected, validate
from t2s.llm import MockLLM

agent = Agent()


@pytest.mark.parametrize("sql", ["DROP TABLE fact_sales", "SELECT * FROM hr_salaries", "SELECT 1; SELECT 2",
                                 "DELETE FROM fact_sales", "SELECT nope FROM fact_sales"])
def test_guard_blocks(sql):
    with pytest.raises(SQLRejected):
        validate(sql, ALLOW)


def test_guard_enforces_row_limit():
    assert "LIMIT 1000" in validate("SELECT sale_id FROM fact_sales", ALLOW)
    assert "LIMIT 1000" in validate("SELECT sale_id FROM fact_sales LIMIT 999999", ALLOW)


def test_semantic_compile_joins_and_filters():
    sql = semantic_compile("revenue by category in 2025")
    assert "JOIN dim_product" in sql and "dim_date.year = 2025" in sql


def test_agent_answers():
    r = agent.ask("revenue by region")
    assert r.error is None and len(r.rows) == 4


def test_self_correction_after_bad_sql():
    replies = iter(["```sql\nSELECT * FROM hr_salaries\n```", "```sql\nSELECT SUM(net_amount) AS revenue FROM fact_sales\n```"])
    llm = MockLLM(lambda p, s: next(replies))
    r = Agent(agent.db, llm).ask("total revenue")
    assert r.attempts == 2 and r.error is None
    assert "guardrail" in llm.calls[1]


def test_gives_up_after_max_attempts():
    r = Agent(agent.db, MockLLM(lambda p, s: "DROP TABLE x")).ask("x")
    assert r.error and r.attempts == 3


def test_snowflake_adapter_with_mock_connector(monkeypatch):
    monkeypatch.setenv("SNOWFLAKE_ROLE", "ANALYST_RO")
    con = MagicMock()
    con.cursor.return_value.fetchall.return_value = [(1,)]
    connect = MagicMock(return_value=con)
    assert SnowflakeAdapter(connect).query("SELECT 1") == [(1,)]
    assert connect.call_args.kwargs["role"] == "ANALYST_RO"


def test_databricks_adapter_with_mock_connector():
    con = MagicMock()
    con.cursor.return_value.__enter__.return_value.fetchall.return_value = [(2,)]
    assert DatabricksAdapter(MagicMock(return_value=con)).query("SELECT 2") == [(2,)]


def test_benchmark_floor():
    r = run(agent)
    assert r["execution_accuracy"] >= 0.75 and r["guardrail_block_rate"] == 1.0
