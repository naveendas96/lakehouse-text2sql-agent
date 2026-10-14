# ADR 0003: Bounded self-correction
**Decision:** On a guardrail rejection or execution error, feed the error message and the failed SQL back to the LLM. At most 3 attempts, then return a structured error. Never return a guess.
**Consequences:** Latency and cost on failure are at most 3 times the single-shot cost, and the failure stays visible to the user.
