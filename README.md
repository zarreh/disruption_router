# A7 — AI-Powered Shipment Disruption Router

> Grounded exception routing for logistics disruptions.

Portfolio app **A7** (`PORTFOLIO_PLAN_V3.md` §?). Supply Chain / Logistics,
Pillar 1 — Regulated Decision Automation. Target URL: `logistics.zarreh.ai`
(not deployed yet).

Takes a shipment disruption event (delay, damage, lost, wrong route, carrier
failure, weather, port strike, etc.) and routes it to the correct exception
handler — **re-route, expedite, claim, cancel, standard recovery** — with every
recommendation traceable to the typed clauses in a versioned rulebook. A human
review layer (HITL) gates high-stakes or low-confidence decisions before the
final action is emitted.

## Status

**Phase 0 scaffold is complete.** Directory structure, packaging, CI skeleton,
and a walking-skeleton LangGraph with SQLite `SqliteSaver` persistence are in
place. The source notebook, rulebook, and test CSV live under `reference/`
(local-only, gitignored).

## Running it locally

```bash
uv sync --extra dev
cp .env.example .env   # fill in your OpenAI API key
make test
make dev               # http://localhost:8000/healthz
```

## Layout

| Path | Purpose |
|---|---|
| `docs/` | MkDocs + Material site — architecture, ADRs, evidence |
| `docs/PLAN.md` | Build plan — phases, architecture, decisions, risks |
| `docs/HARVEST.md` | Implementation log and harvestable insights |
| `src/router/` | Application — `api/`, `graph/`, `tools/`, `schemas/`, `settings.py` |
| `data/` | Rulebook builder and scenario fixtures |
| `evals/` | Canonical evaluation harness |
| `tests/` | Backend test suite |
| `reference/` | Local-only source material. **Gitignored**, never published |
