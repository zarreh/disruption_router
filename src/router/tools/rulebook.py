import json
from functools import lru_cache
from pathlib import Path

from router.schemas.rulebook import Clause, Rulebook
from router.schemas.state import RuleMatch


def load_rulebook(path: str | Path = "data/rulebook.json") -> Rulebook:
    """Load the typed, versioned rulebook from JSON."""
    with open(path) as f:
        return Rulebook.model_validate(json.load(f))


@lru_cache(maxsize=1)
def get_rulebook(path: str | Path = "data/rulebook.json") -> Rulebook:
    return load_rulebook(path)


def lookup_clauses(
    event_type: str,
    severity: str,
    path: str | Path = "data/rulebook.json",
) -> list[RuleMatch]:
    """Structured clause lookup by event_type and severity.

    This is intentionally deterministic and keyword-driven rather than vector-
    based: every recommendation must cite exact clause text. See ADR D-A7-1.
    """
    rulebook = get_rulebook(path)
    matches: list[RuleMatch] = []
    event_l = event_type.lower()
    severity_l = severity.lower()
    for clause in rulebook.clauses:
        events = clause.event_types.lower()
        severities = clause.severities.lower()
        if event_l in events and severity_l in severities:
            matches.append(
                RuleMatch(
                    clause_id=clause.id,
                    clause_text=clause.text,
                    action=clause.action,
                    confidence="high" if severity_l == "critical" else "medium",
                    reason=f"Matched {event_type}/{severity} against clause {clause.id}",
                )
            )
    return matches


def all_clauses(path: str | Path = "data/rulebook.json") -> list[Clause]:
    """Return every clause in the rulebook."""
    return get_rulebook(path).clauses
