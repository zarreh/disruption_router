# A7 — AI-Powered Shipment Disruption Router

Grounded exception routing for logistics disruptions.

## What it does

Given a disruption event, the router:

1. **Ingests** the shipment report.
2. **Retrieves** matching clauses from a typed, versioned rulebook.
3. **Routes** to the correct action with a structured recommendation.
4. **Pauses for human review** when severity or confidence demands it.
5. **Publishes** a final, traceable decision.

## Key design decisions

- [D-A7-1: Structured clause lookup](architecture/decisions/D-A7-1-structured-clause-lookup.md)
- [D-A7-2: SQLite SqliteSaver](architecture/decisions/D-A7-2-sqlite-saver.md)
