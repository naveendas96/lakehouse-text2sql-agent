.PHONY: install test bench demo
install: ; pip install -e ".[dev]"
test: ; pytest -q
bench: ; t2s bench
demo: ; t2s ask "total revenue by region"
