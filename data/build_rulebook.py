"""Build a typed, versioned rulebook JSON from the source text artifact."""

import re
from datetime import UTC, datetime
from pathlib import Path

from router.schemas.rulebook import Clause, Policy, Rulebook

RULEBOOK_TEXT = Path("reference/logistics_policy_rulebook.txt")
OUTPUT = Path("data/rulebook.json")


def _split_policies(text: str) -> list[dict[str, str]]:
    """Split the raw rulebook text into policy blocks."""
    # Each policy starts with POL-NNN: Title and ends before the next POL- or EOF.
    pattern = re.compile(r"(POL-\d+):\s*(.+?)\n(.*?)(?=\nPOL-\d+:|\Z)", re.DOTALL)
    policies: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        pid, name, body = match.groups()
        policies.append({"id": pid, "name": name.strip(), "body": body.strip()})
    return policies


def _extract_field(body: str, label: str) -> str:
    pattern = re.compile(rf"{label}:\s*(.*?)(?=\n[A-Z][a-z].*?:|\Z)", re.DOTALL)
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def parse_policies(text: str) -> list[Policy]:
    """Parse raw policy blocks into typed Policy models."""
    policies: list[Policy] = []
    for block in _split_policies(text):
        body = block["body"]
        scope = _extract_field(body, "Scope")
        standard_action = _extract_field(body, "Standard Action")
        policies.append(
            Policy(
                id=block["id"],
                name=block["name"],
                scope=scope,
                standard_action=standard_action,
                raw_text=body,
            )
        )
    return policies


def derive_clauses(policies: list[Policy]) -> list[Clause]:
    """Derive flat, routable clauses from the parsed policies.

    This encodes the operational intent of each policy in a form that the
    structured clause lookup can match against an incoming disruption report.
    """
    clauses: list[Clause] = []

    # POL-001: Weather Disruption Protocol
    clauses.extend(
        [
            Clause(
                id="C-001A",
                policy_id="POL-001",
                text="Weather-related delay under 3 days: monitor status and hold at current hub.",
                action="monitor",
                event_types="weather,delay",
                severities="low",
                conditions={"max_delay_days": 2},
            ),
            Clause(
                id="C-001B",
                policy_id="POL-001",
                text="Weather-related delay 3-5 days: reroute via alternate regional hub.",
                action="reroute",
                event_types="weather,delay",
                severities="medium",
                conditions={"min_delay_days": 3, "max_delay_days": 5},
            ),
            Clause(
                id="C-001C",
                policy_id="POL-001",
                text="Weather-related delay over 5 days: escalate to senior dispatch.",
                action="escalate_human",
                event_types="weather,delay",
                severities="high,critical",
                conditions={"min_delay_days": 6},
            ),
        ]
    )

    # POL-002: Standard Late Delivery Protocol
    clauses.extend(
        [
            Clause(
                id="C-002A",
                policy_id="POL-002",
                text="Late delivery 2-5 days with alternate carrier available: reroute.",
                action="reroute",
                event_types="late_delivery,delay",
                severities="medium,high",
                conditions={"min_delay_days": 2, "max_delay_days": 5},
            ),
            Clause(
                id="C-002B",
                policy_id="POL-002",
                text="Late delivery 2-5 days with no alternate carrier: hold and expedite.",
                action="expedite",
                event_types="late_delivery,delay",
                severities="medium,high",
                conditions={"min_delay_days": 2, "max_delay_days": 5, "alternate_available": False},
            ),
            Clause(
                id="C-002C",
                policy_id="POL-002",
                text="High-value shipment (sales > $3,000) with late delivery risk: expedite.",
                action="expedite",
                event_types="late_delivery,delay",
                severities="medium,high,critical",
                conditions={"sales_above": 3000},
            ),
        ]
    )

    # POL-003: Critical Escalation Policy
    clauses.extend(
        [
            Clause(
                id="C-003A",
                policy_id="POL-003",
                text="Shipping canceled: management intervention required.",
                action="escalate_human",
                event_types="canceled",
                severities="high,critical",
            ),
            Clause(
                id="C-003B",
                policy_id="POL-003",
                text="Extreme delay exceeding 5 calendar days: management intervention required.",
                action="escalate_human",
                event_types="delay,late_delivery",
                severities="critical",
                conditions={"min_delay_days": 6},
            ),
            Clause(
                id="C-003C",
                policy_id="POL-003",
                text="High-value shipment with late delivery risk: escalate for management review.",
                action="escalate_human",
                event_types="late_delivery,delay",
                severities="high,critical",
                conditions={"sales_above": 3000},
            ),
            Clause(
                id="C-003D",
                policy_id="POL-003",
                text="Corporate customer SLA breach imminent (<4 hours): escalate immediately.",
                action="escalate_human",
                event_types="sla_breach",
                severities="critical",
                conditions={"customer_segment": "Corporate", "hours_to_breach": 4},
            ),
        ]
    )

    # POL-004: Shipping Mode SLA Commitments
    clauses.extend(
        [
            Clause(
                id="C-004A",
                policy_id="POL-004",
                text="Same Day shipping mode SLA breach: expedite.",
                action="expedite",
                event_types="sla_breach,delay",
                severities="high,critical",
                conditions={"shipping_mode": "Same Day"},
            ),
            Clause(
                id="C-004B",
                policy_id="POL-004",
                text="First Class shipping mode SLA breach: expedite.",
                action="expedite",
                event_types="sla_breach,delay",
                severities="high",
                conditions={"shipping_mode": "First Class"},
            ),
            Clause(
                id="C-004C",
                policy_id="POL-004",
                text="Second Class shipping mode SLA breach: reroute.",
                action="reroute",
                event_types="sla_breach,delay",
                severities="medium,high",
                conditions={"shipping_mode": "Second Class"},
            ),
            Clause(
                id="C-004D",
                policy_id="POL-004",
                text="Standard Class shipping mode SLA breach: hold.",
                action="hold",
                event_types="sla_breach,delay",
                severities="low,medium",
                conditions={"shipping_mode": "Standard Class"},
            ),
            Clause(
                id="C-004E",
                policy_id="POL-004",
                text=(
                    "Shipment within 1 day of SLA tolerance threshold: "
                    "monitor with priority review."
                ),
                action="monitor",
                event_types="delay",
                severities="low,medium",
                conditions={"days_to_tolerance": 1},
            ),
        ]
    )

    # POL-005: Customer Segment Priority Matrix
    clauses.extend(
        [
            Clause(
                id="C-005A",
                policy_id="POL-005",
                text=(
                    "Corporate customer in routing conflict or capacity "
                    "shortage: prioritize reroute/expedite."
                ),
                action="reroute",
                event_types="routing_conflict,capacity_issue",
                severities="medium,high",
                conditions={"customer_segment": "Corporate"},
            ),
            Clause(
                id="C-005B",
                policy_id="POL-005",
                text="Home Office order over $2,000: inherit Corporate priority handling.",
                action="reroute",
                event_types="routing_conflict,capacity_issue,late_delivery",
                severities="medium,high",
                conditions={"customer_segment": "Home Office", "sales_above": 2000},
            ),
        ]
    )

    # POL-006: Special Cargo Handling Protocols
    clauses.extend(
        [
            Clause(
                id="C-006A",
                policy_id="POL-006",
                text="Electronics delay over 2 days: reroute via temperature-controlled lane.",
                action="reroute",
                event_types="delay,electronics",
                severities="medium,high",
                conditions={"category": "Electronics", "min_delay_days": 3},
            ),
            Clause(
                id="C-006B",
                policy_id="POL-006",
                text="Furniture delay up to 5 days: monitor; avoid rerouting due to bulk cost.",
                action="monitor",
                event_types="delay,furniture",
                severities="low,medium",
                conditions={"category": "Furniture", "max_delay_days": 5},
            ),
            Clause(
                id="C-006C",
                policy_id="POL-006",
                text="Clothing within 7 days of seasonal transition: expedite.",
                action="expedite",
                event_types="delay,clothing",
                severities="medium,high",
                conditions={"category": "Clothing", "days_to_season": 7},
            ),
            Clause(
                id="C-006D",
                policy_id="POL-006",
                text="Sports goods: follow standard handling procedures.",
                action="monitor",
                event_types="delay,sports",
                severities="low,medium",
                conditions={"category": "Sports"},
            ),
            Clause(
                id="C-006E",
                policy_id="POL-006",
                text="Books: lowest priority filler capacity on alternate routes.",
                action="monitor",
                event_types="delay,books",
                severities="low",
                conditions={"category": "Books"},
            ),
        ]
    )

    return clauses


def build() -> Rulebook:
    text = RULEBOOK_TEXT.read_text()
    policies = parse_policies(text)
    clauses = derive_clauses(policies)
    return Rulebook(
        version="1.0.0",
        source=str(RULEBOOK_TEXT),
        generated_at=datetime.now(UTC).isoformat(),
        policies=policies,
        clauses=clauses,
    )


def main() -> None:
    rulebook = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rulebook.model_dump_json(indent=2))
    clause_count = len(rulebook.clauses)
    policy_count = len(rulebook.policies)
    print(f"Wrote {clause_count} clauses from {policy_count} policies to {OUTPUT}")


if __name__ == "__main__":
    main()
