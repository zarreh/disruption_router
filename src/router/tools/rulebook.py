import json
from functools import lru_cache
from pathlib import Path

from router.schemas.rulebook import Clause, Rulebook
from router.schemas.state import DisruptionEvent, RuleMatch


def load_rulebook(path: str | Path = "data/rulebook.json") -> Rulebook:
    """Load the typed, versioned rulebook from JSON."""
    with open(path) as f:
        return Rulebook.model_validate(json.load(f))


@lru_cache(maxsize=1)
def get_rulebook(path: str | Path = "data/rulebook.json") -> Rulebook:
    return load_rulebook(path)


def _condition_matches(clause: Clause, event: DisruptionEvent | None) -> bool:
    """Check whether an event satisfies the clause's additional guards."""
    if event is None or not clause.conditions:
        return not clause.conditions

    for key, value in clause.conditions.items():
        if key == "sales_above":
            if event.sales is None or event.sales <= float(value):
                return False
        elif key == "min_delay_days":
            if event.delay_days is None or event.delay_days < int(value):
                return False
        elif key == "max_delay_days":
            if event.delay_days is None or event.delay_days > int(value):
                return False
        elif key == "shipping_mode":
            if event.shipping_mode != str(value):
                return False
        elif key == "customer_segment":
            if event.customer_tier != str(value):
                return False
        elif key == "category":
            if event.category != str(value):
                return False
        elif key == "alternate_available":
            if event.alternate_available is None or event.alternate_available != bool(value):
                return False
        elif key in {"days_to_tolerance", "days_to_season"}:
            field_value = getattr(event, key, None)
            if field_value is None or int(field_value) > int(value):
                return False
        else:
            field_value = getattr(event, key, None)
            if field_value is None or field_value != value:
                return False
    return True


def lookup_clauses(
    event_type: str,
    severity: str,
    path: str | Path = "data/rulebook.json",
    event: DisruptionEvent | None = None,
) -> list[RuleMatch]:
    """Structured clause lookup by event_type, severity, and optional guards.

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
        if event_l in events and severity_l in severities and _condition_matches(clause, event):
            matches.append(
                RuleMatch(
                    clause_id=clause.id,
                    clause_text=clause.text,
                    action=clause.action,
                    confidence="high" if severity_l == "critical" else "medium",
                    reason=f"Matched {event_type}/{severity} against clause {clause.id}",
                    priority=clause.priority,
                )
            )
    matches.sort(key=lambda m: m.priority, reverse=True)
    return matches


def all_clauses(path: str | Path = "data/rulebook.json") -> list[Clause]:
    """Return every clause in the rulebook."""
    return get_rulebook(path).clauses
