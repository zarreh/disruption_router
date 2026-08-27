# Evaluation

## Layer 1 — canonical scenarios

`evals/run.py` runs 15 canonical scenarios covering every action class and
several edge cases. Each scenario supplies a `DisruptionEvent` and an expected
action. The graph is invoked and the resulting `RouteRecommendation.action` is
compared to the expected value.

```bash
make eval
```

## Latest result

- **15/15 correct (100.0%)**
- Actions covered: `monitor`, `reroute`, `expedite`, `escalate_human`, `hold`
- Edge cases covered: no matching clause, high-value override, category-specific
  handling, customer-segment priority.

## Limitations

- These scenarios exercise the deterministic fallback and the grounding judge.
  The LLM path is evaluated manually when `ROUTER_OPENAI_API_KEY` is provided.
- Layer 1 is a correctness smoke test, not a statistically powered measure of
  precision/recall on real-world traffic.
