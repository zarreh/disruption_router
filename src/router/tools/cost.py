"""Cost and impact estimation helpers for routing decisions."""

from router.schemas.state import DisruptionEvent


def estimate_delay_cost(event: DisruptionEvent, delay_days: int) -> float:
    """Estimate carrier delay cost for a disruption event.

    This is a placeholder model: $50/day base + 1% of imputed shipment value per
    day for high/critical severity.
    """
    base = 50.0 * max(delay_days, 1)
    if event.severity in {"high", "critical"}:
        base += 0.01 * 1000.0 * delay_days
    return round(base, 2)
