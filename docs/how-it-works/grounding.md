# Grounding

A grounded routing decision is one whose justification can be checked against
retrieved evidence. In this app the evidence is the set of matched rulebook
clauses.

## Grounding checks

The `judge_grounding` node enforces two rules:

1. **Cited clauses must be retrieved.** The recommendation's
   `matched_clauses` must be a subset of the clauses returned by the structured
   lookup.
2. **Action must be supported.** The chosen action must appear in at least one
   of the retrieved clauses.

If either check fails, the graph loops back to `route` with the failure reason.
After `max_iterations` the graph publishes its best-effort recommendation so it
never silently hangs.

## Why structured lookup, not vector search

See ADR [D-A7-1](../architecture/decisions/D-A7-1-structured-clause-lookup.md).
The short version: a small, typed rulebook allows exact, reproducible retrieval
and makes every citation auditable.
