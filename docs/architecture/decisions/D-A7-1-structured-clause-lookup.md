# D-A7-1 — Structured clause lookup instead of vector retrieval

## Context

The source notebook routes shipment disruptions by consulting a rulebook of
logistics clauses. A natural reflex is to embed the clauses and retrieve by
semantic similarity, but the rulebook is small, clause language is precise, and
the portfolio already has vector-search apps (A2 deliberately avoided one).

## Decision

Use a typed, versioned JSON rulebook and match clauses by structured keys
(`event_types`, `severities`, optionally `customer_tier`, `carrier_type`). The
LLM still generates the recommendation and justification, but every citation is
checked against the exact clause text retrieved by deterministic lookup.

## Consequences

- **Pros:** Fully reproducible, no embedding cost, no vector-store dependency,
easy to audit, small cold-start.
- **Cons:** Does not generalize to unseen event language; rulebook must be kept
current.

## Related

Cites D-A3-5 from the portfolio plan (retrieval design for grounded
regulatory/logistics decisions).
