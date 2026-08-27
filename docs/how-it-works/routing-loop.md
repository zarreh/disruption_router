# The routing loop

When a disruption report arrives, the router does not immediately emit an
action. It runs a short, repeatable loop:

1. **Retrieve clauses** that match the event type, severity, and any extra
   guards (category, sales value, delay days, shipping mode).
2. **Generate a recommendation** with the LLM (or deterministic fallback).
3. **Judge grounding**: did the recommendation cite only clauses that were
   actually retrieved? Is the action supported by at least one retrieved clause?
4. If grounding fails and iterations remain, **retry the route** with the
   judge's feedback.
5. If grounding passes, either **publish** directly or pause for **human
   review** when severity or confidence demands it.

This loop is what makes the router grounded: every action must be traceable to
a clause in the typed, versioned rulebook.
