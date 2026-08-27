# A7 Disruption Router — Implementation Log

## 2025-06-02 — Phase 0 scaffold

- Transplanted A2 (`trade_surveillance_agent`) skeleton into `disruption_router/`.
- Renamed package `surveillance` → `router`, env prefix `SURVEILLANCE_` →
`ROUTER_`, URL `surveillance.zarreh.ai` → `logistics.zarreh.ai`.
- Chose `SqliteSaver` for durable HITL interrupts (D-A7-2).
- Chose deterministic structured clause lookup for retrieval (D-A7-1).
- Walking-skeleton graph compiles with `ingest → retrieve → route → publish` and
conditional HITL edge.

## 2026-08-27 — Phase 1 rulebook as code

- Added `src/router/schemas/rulebook.py` with typed `Policy`, `Clause`, and
`Rulebook` models.
- Added `data/build_rulebook.py` that parses `reference/logistics_policy_rulebook.txt`
into 6 policies and 22 routable clauses.
- `make data` now regenerates `data/rulebook.json` deterministically.
- Aligned `RouteRecommendation.action` vocabulary with the source rulebook:
`monitor | reroute | expedite | escalate_human | hold | cancel`.

## 2026-08-27 — Phase 2 LLM router + grounding judge

- Added `src/router/graph/llm.py` with `get_llm()` factory (returns `None` when
no `ROUTER_OPENAI_API_KEY` is set).
- Replaced deterministic vote in `route` with LLM structured output
(`RouteRecommendation`) when a key is available, with deterministic fallback.
- Added `judge_grounding` node that verifies cited clauses exist in the
retrieved set and the action is supported by at least one matched clause.
- Graph now loops `route -> judge_grounding -> route` up to `max_iterations`
on grounding failure.
- Added `src/router/tools/cost.py` stub for delay-cost estimation.

## Harvested patterns

- A2's `AgentSettings` from `zarreh_agentkit` gives us OpenAI + LangSmith env
loading for free; keep using it.
- Import-linter contracts catch accidental graph↔tools coupling early.
- Keep rulebook actions in one flat enum shared between the typed schema and the
LLM structured-output description to avoid drift.
