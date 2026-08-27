# A7 Disruption Router — Implementation Log

## 2025-06-02 — Phase 0 scaffold

- Transplanted A2 (`trade_surveillance_agent`) skeleton into `disruption_router/`.
- Renamed package `surveillance` → `router`, env prefix `SURVEILLANCE_` →
`ROUTER_`, URL `surveillance.zarreh.ai` → `logistics.zarreh.ai`.
- Chose `SqliteSaver` for durable HITL interrupts (D-A7-2).
- Chose deterministic structured clause lookup for retrieval (D-A7-1).
- Walking-skeleton graph compiles with `ingest → retrieve → route → publish` and
conditional HITL edge.

## Harvested patterns

- A2's `AgentSettings` from `zarreh_agentkit` gives us OpenAI + LangSmith env
loading for free; keep using it.
- Import-linter contracts catch accidental graph↔tools coupling early.
