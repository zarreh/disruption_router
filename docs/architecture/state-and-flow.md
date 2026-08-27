# State and flow

## State schema

`RouterState` carries the disruption event, matched rulebook clauses, the
current recommendation, and grounding-loop metadata.

```python
class RouterState(BaseModel):
    messages: Annotated[list[Any], add_messages]
    event: DisruptionEvent | None = None
    candidate_action: str | None = None
    recommendation: RouteRecommendation | None = None
    human_decision: str | None = None
    grounding_passed: bool = False
    grounding_feedback: str = ""
    iteration: int = 0
    max_iterations: int = 3
```

## Node responsibilities

- **ingest**: Normalizes the incoming event.
- **retrieve**: Looks up matching rulebook clauses using structured keys and
  optional guards (sales, delay_days, shipping_mode, etc.).
- **route**: Generates a `RouteRecommendation`. Uses an LLM with structured
  output when `ROUTER_OPENAI_API_KEY` is set; otherwise falls back to a
  priority-based deterministic vote.
- **judge_grounding**: Verifies that cited clause IDs exist in the retrieved
  set and that the recommended action is supported by at least one matched
  clause. Failed checks loop back to `route` with feedback.
- **human_review**: `interrupt()` for high-stakes or low-confidence decisions.
- **publish**: Emits the final action.
