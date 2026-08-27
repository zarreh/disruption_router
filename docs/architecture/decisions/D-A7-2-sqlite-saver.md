# D-A7-2 — SQLite SqliteSaver for durable HITL

## Context

The router must pause for human approval on high-stakes or low-confidence
routes. LangGraph provides `interrupt()` for HITL, but the checkpoint store must
outlive the process so reviews can be resumed after deploys or crashes.

## Decision

Persist checkpoints with LangGraph's `SqliteSaver` backed by a local SQLite file
(`data/runs.sqlite`). This satisfies durable interrupts without requiring
Postgres, Redis, or external services.

## Consequences

- **Pros:** Zero external infrastructure, simple backups, works in Docker and
CI.
- **Cons:** Not horizontally scalable; if multi-replica deployment is needed
later, switch to Postgres checkpointer.
