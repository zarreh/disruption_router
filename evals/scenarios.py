"""Canonical evaluation scenarios for the disruption router."""

from router.schemas.state import DisruptionEvent


class Scenario:
    """A single eval case."""

    def __init__(
        self,
        *,
        id: str,
        event: DisruptionEvent,
        expected_action: str,
        notes: str = "",
    ) -> None:
        self.id = id
        self.event = event
        self.expected_action = expected_action
        self.notes = notes


SCENARIOS: list[Scenario] = [
    Scenario(
        id="standard_delay_low",
        event=DisruptionEvent(
            shipment_id="EV-001",
            event_type="delay",
            severity="low",
            description="Minor standard-class delay, no SLA breach.",
        ),
        expected_action="monitor",
        notes="Generic low-severity delay falls back to monitor.",
    ),
    Scenario(
        id="late_delivery_reroute",
        event=DisruptionEvent(
            shipment_id="EV-002",
            event_type="late_delivery",
            severity="medium",
            description="Late delivery with alternate carrier available.",
            delay_days=3,
        ),
        expected_action="reroute",
        notes="POL-002: reroute when delay is 2-5 days.",
    ),
    Scenario(
        id="canceled_escalate",
        event=DisruptionEvent(
            shipment_id="EV-003",
            event_type="canceled",
            severity="critical",
            description="Shipping canceled by carrier.",
        ),
        expected_action="escalate_human",
        notes="POL-003: any cancellation requires management intervention.",
    ),
    Scenario(
        id="high_value_expedite",
        event=DisruptionEvent(
            shipment_id="EV-004",
            event_type="late_delivery",
            severity="high",
            description="High-value corporate electronics shipment is late.",
            sales=3500.0,
            delay_days=2,
            customer_tier="Corporate",
            category="Electronics",
        ),
        expected_action="expedite",
        notes="POL-002 high-value clause wins over generic escalation.",
    ),
    Scenario(
        id="electronics_reroute",
        event=DisruptionEvent(
            shipment_id="EV-005",
            event_type="electronics",
            severity="medium",
            description="Electronics delay over 2 days, temperature control needed.",
            category="Electronics",
            delay_days=3,
        ),
        expected_action="reroute",
        notes="POL-006: electronics delay >2 days reroute via temp-controlled lane.",
    ),
    Scenario(
        id="weather_reroute",
        event=DisruptionEvent(
            shipment_id="EV-006",
            event_type="weather",
            severity="medium",
            description="Adverse weather causing 4-day delay.",
            delay_days=4,
        ),
        expected_action="reroute",
        notes="POL-001: weather delay 3-5 days triggers reroute.",
    ),
    Scenario(
        id="weather_escalate",
        event=DisruptionEvent(
            shipment_id="EV-007",
            event_type="weather",
            severity="critical",
            description="Severe weather causing 6-day delay.",
            delay_days=6,
        ),
        expected_action="escalate_human",
        notes="POL-001: weather delay >5 days escalates to senior dispatch.",
    ),
    Scenario(
        id="sla_second_class_reroute",
        event=DisruptionEvent(
            shipment_id="EV-008",
            event_type="sla_breach",
            severity="medium",
            description="Second Class SLA breach.",
            shipping_mode="Second Class",
        ),
        expected_action="reroute",
        notes="POL-004: Second Class breach action is reroute.",
    ),
    Scenario(
        id="corporate_conflict_reroute",
        event=DisruptionEvent(
            shipment_id="EV-009",
            event_type="routing_conflict",
            severity="medium",
            description="Corporate customer affected by limited route capacity.",
            customer_tier="Corporate",
        ),
        expected_action="reroute",
        notes="POL-005: Corporate customers get prioritized reroute/expedite.",
    ),
    Scenario(
        id="furniture_monitor",
        event=DisruptionEvent(
            shipment_id="EV-010",
            event_type="furniture",
            severity="low",
            description="Furniture delay within tolerable window.",
            category="Furniture",
            delay_days=3,
        ),
        expected_action="monitor",
        notes="POL-006: furniture delay up to 5 days should be monitored.",
    ),
    Scenario(
        id="books_monitor",
        event=DisruptionEvent(
            shipment_id="EV-011",
            event_type="books",
            severity="low",
            description="Books shipment delay, lowest priority filler.",
            category="Books",
        ),
        expected_action="monitor",
        notes="POL-006: books are lowest priority.",
    ),
    Scenario(
        id="unknown_event_monitor",
        event=DisruptionEvent(
            shipment_id="EV-012",
            event_type="alien_invasion",
            severity="low",
            description="Unknown disruption type not covered by rulebook.",
        ),
        expected_action="monitor",
        notes="No clauses match; fallback to monitor with human review.",
    ),
    Scenario(
        id="standard_class_sla_hold",
        event=DisruptionEvent(
            shipment_id="EV-013",
            event_type="sla_breach",
            severity="low",
            description="Standard Class SLA breach.",
            shipping_mode="Standard Class",
        ),
        expected_action="hold",
        notes="POL-004: Standard Class breach action is hold.",
    ),
    Scenario(
        id="same_day_expedite",
        event=DisruptionEvent(
            shipment_id="EV-014",
            event_type="sla_breach",
            severity="critical",
            description="Same Day delivery SLA breach.",
            shipping_mode="Same Day",
        ),
        expected_action="expedite",
        notes="POL-004: Same Day breach action is expedite.",
    ),
    Scenario(
        id="home_office_high_value_reroute",
        event=DisruptionEvent(
            shipment_id="EV-015",
            event_type="routing_conflict",
            severity="medium",
            description="Home Office order over $2,000 in capacity shortage.",
            customer_tier="Home Office",
            sales=2500.0,
        ),
        expected_action="reroute",
        notes="POL-005: Home Office >$2,000 inherits Corporate priority.",
    ),
]
