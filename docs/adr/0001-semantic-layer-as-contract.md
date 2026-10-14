# ADR 0001: The semantic layer is the agent's contract
**Decision:** The LLM only sees `semantic.yaml`: allowed tables, join paths and certified metric SQL (for example `revenue = SUM(net_amount)`). It never sees the raw catalog.
**Why:** Most text-to-SQL errors come from the wrong metric definition or a wrong join. Certified definitions fix both and give one place to govern them.
**Consequences:** New questions may need new metrics or dimensions added. That's an intentional governance step.
