# A7 Disruption Router — Build Plan

Source notebook: `reference/AI_Powered_Shipment_Disruption_Router_V1_1.ipynb`
Rulebook & data: `reference/`

## Decisions already confirmed

1. **Retrieval = structured clause lookup**, not vector search. The rulebook is a
typed, versioned JSON artifact; matches are by `event_type`/`severity` keys.
ADR: [D-A7-1](architecture/decisions/D-A7-1-structured-clause-lookup.md).
2. **Persistence = SQLite `SqliteSaver`**. Durable HITL interrupts with no extra
infra. ADR: [D-A7-2](architecture/decisions/D-A7-2-sqlite-saver.md).
3. **No Chroma, no HuggingFace, no MemorySaver**. Aligns with source notebook and
keeps the dependency footprint small.
4. **Package name `router`**, env prefix `ROUTER_`, target URL
`logistics.zarreh.ai`.

## Phases

### Phase 0 — Scaffold (this commit)
- [x] Directory tree, `pyproject.toml`, `Makefile`, `Dockerfile`, `compose.yaml`, `mkdocs.yml`
- [x] `src/router/` package skeleton: `api/`, `graph/`, `tools/`, `schemas/`, `settings.py`
- [x] Walking-skeleton graph: ingest → retrieve → route → (HITL) → publish
- [x] Smoke tests, CI workflow, docs/PLAN.md, docs/HARVEST.md
- [x] Source material copied to `reference/`

**Exit criteria:** `make test` passes; `make dev` healthz returns 200; CI green.

### Phase 1 — Rulebook as code
- Build `data/build_rulebook.py` that parses the source rulebook CSV/XLSX into a
versioned, typed JSON schema.
- Add rulebook schema validation (Pydantic).
- Add `reference/.gitkeep` semantics; keep raw source local-only.

**Exit criteria:** `make data` regenerates `data/rulebook.json`; rulebook tests
assert every clause has id/text/action/event_types/severities.

### Phase 2 — Reasoning nodes ✅
- [x] Replace deterministic vote in `route` with an LLM node that generates
`RouteRecommendation` via Pydantic structured output.
- [x] Add grounding: recommendation must cite clause IDs; a judge node checks that
cited clauses exist and support the action.
- [x] Add cost/impact estimation tool stub (carrier delay cost, customer-tier
penalty).

**Exit criteria:** Evaluation harness (`make eval`) shows ≥85% route accuracy on
10 canonical scenarios with grounded justifications.

### Phase 3 — HITL queue ✅
- [x] Implement `/reviews` endpoint returning interrupted threads awaiting human
decision.
- [x] Add `POST /reviews/{thread_id}` to resume graph with override.
- [x] Minimal Next.js review UI under `frontend/`.

**Exit criteria:** Playwright or API test demonstrates submit → interrupt →
resume → publish flow.

### Phase 4 — API + observability ✅
- [x] SSE stream for graph events (`POST /route/stream`).
- [x] Structured logging with `structlog`.
- [x] LangSmith tracing integration via `zarreh_agentkit` (enabled when
`ROUTER_LANGSMITH_API_KEY` is set).

**Exit criteria:** `/route` stream emits node-enter/exit events; traces visible
in LangSmith project.

### Phase 5 — Evaluation + documentation ✅
- [x] Layer 1 canonical eval with 15 scenarios covering each action class and
edge cases (no match, tie, critical escalation).
- [x] Publish MkDocs site; architecture pages, ADRs, evidence.

**Exit criteria:** `make eval` gates PRs; `mkdocs build --strict` passes.

### Phase 6 — Deployment prep (deferred until DNS/VPS ready)
- Caddy + Docker Compose on VPS; `logistics.zarreh.ai`.
- HTTPS, health checks, `.env` secret management.

## Risks

- Rulebook source format may be messy (CSV with merged cells). Mitigation: parse
with `pandas` and validate schema strictly.
- LLM may hallucinate clause IDs. Mitigation: grounding judge + structured
lookup.
- HITL interrupt model changes across LangGraph versions. Mitigation: pin
`langgraph>=0.2,<0.3` and test with `SqliteSaver`.

## Open questions

- DNS/VPS setup for `logistics.zarreh.ai`: same Caddy pattern as A2 or new?
- Should HITL interrupt land earlier, e.g. after retrieve for critical events?
