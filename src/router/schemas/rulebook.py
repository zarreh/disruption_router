"""Typed rulebook schema."""

from pydantic import BaseModel, Field


class Policy(BaseModel):
    """A source policy extracted from the logistics rulebook text."""

    id: str = Field(..., description="Policy identifier, e.g. POL-001")
    name: str
    scope: str
    standard_action: str
    raw_text: str


class Clause(BaseModel):
    """A routable clause derived from one or more policies."""

    id: str
    policy_id: str
    text: str
    action: str = Field(
        ..., description="monitor | reroute | expedite | escalate_human | hold | cancel"
    )
    event_types: str = Field(
        ..., description="Comma-separated event-type keywords matched against the report"
    )
    severities: str = Field(
        ..., description="Comma-separated severity keywords matched against the report"
    )
    conditions: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="Additional numeric or categorical guards (e.g. min_delay_gap, sales_above)",
    )


class Rulebook(BaseModel):
    """Versioned, typed rulebook artifact."""

    version: str
    source: str
    generated_at: str
    policies: list[Policy]
    clauses: list[Clause]
