"""Deterministic synthetic retail star schema in DuckDB."""
from __future__ import annotations

import random

import duckdb


def build_db(path: str = ":memory:", n_sales: int = 20000, seed: int = 7) -> duckdb.DuckDBPyConnection:
    rnd = random.Random(seed)
    con = duckdb.connect(path)
    con.execute('''CREATE OR REPLACE TABLE dim_date AS SELECT CAST(strftime(d, '%Y%m%d') AS INT) AS date_key, CAST(d AS DATE) AS "date", year(d) AS "year", quarter(d) AS "quarter", month(d) AS "month", monthname(d) AS month_name FROM range(DATE '2024-01-01', DATE '2026-01-01', INTERVAL 1 DAY) t(d)''')
    regions = {"North": ["Delhi", "Chandigarh"], "South": ["Chennai", "Bengaluru"], "East": ["Kolkata", "Bhubaneswar"], "West": ["Mumbai", "Pune"]}
    stores = [(i + 1, f"Store {i + 1:02d}", r, rnd.choice(c)) for i, (r, c) in enumerate([(r, c) for r, c in regions.items() for _ in range(5)])]
    con.execute("CREATE OR REPLACE TABLE dim_store(store_key INT, store_name VARCHAR, region VARCHAR, city VARCHAR)")
    con.executemany("INSERT INTO dim_store VALUES (?,?,?,?)", stores)
    cats = {"Electronics": (["Volt", "Nimbus"], 8000), "Grocery": (["FreshCo", "Harvest"], 300), "Apparel": (["Loom", "Thread"], 1500), "Home": (["Nest", "Hearth"], 2500)}
    prods = [(i + 1, f"{c} Item {i + 1}", c, rnd.choice(b), p * rnd.uniform(0.5, 1.5)) for i, (c, (b, p)) in enumerate([(c, v) for c, v in cats.items() for _ in range(10)])]
    con.execute("CREATE OR REPLACE TABLE dim_product(product_key INT, product_name VARCHAR, category VARCHAR, brand VARCHAR, list_price DOUBLE)")
    con.executemany("INSERT INTO dim_product VALUES (?,?,?,?,?)", prods)
    custs = [(i + 1, rnd.choice(["Consumer", "Business"]), rnd.choices(["Gold", "Silver", "Bronze"], [1, 3, 6])[0]) for i in range(2000)]
    con.execute("CREATE OR REPLACE TABLE dim_customer(customer_key INT, segment VARCHAR, loyalty_tier VARCHAR)")
    con.executemany("INSERT INTO dim_customer VALUES (?,?,?)", custs)
    dates = [r[0] for r in con.execute("SELECT date_key FROM dim_date").fetchall()]
    sales = []
    for i in range(n_sales):
        p = rnd.choice(prods)
        q = rnd.randint(1, 5)
        disc = round(p[4] * q * rnd.choice([0, 0, 0.05, 0.1]), 2)
        sales.append((i + 1, rnd.choice(dates), rnd.choice(stores)[0], p[0], rnd.choice(custs)[0], q, round(p[4] * q - disc, 2), disc))
    con.execute("CREATE OR REPLACE TABLE fact_sales(sale_id INT, date_key INT, store_key INT, product_key INT, customer_key INT, quantity INT, net_amount DOUBLE, discount_amount DOUBLE)")
    con.executemany("INSERT INTO fact_sales VALUES (?,?,?,?,?,?,?,?)", sales)
    con.execute("CREATE OR REPLACE TABLE hr_salaries(employee VARCHAR, salary DOUBLE)")  # not in semantic layer: must be blocked
    return con
