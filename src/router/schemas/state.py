from typing import Annotated, Any

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class DisruptionEvent(BaseModel):
    """Incoming disruption report."""

    shipment_id: str
    event_type: str = Field(description="e.g. delay, damage, lost, wrong_route, carrier_failure")
    severity: str = Field(default="medium", description="low | medium | high | critical")
    description: str
    carrier: str | None = None
    origin: str | None = None
    destination: str | None = None
    customer_tier: str | None = None


class RuleMatch(BaseModel):
    """A matched clause from the rulebook."""

    clause_id: str
    clause_text: str
    action: str
    confidence: str
    reason: str


class RouteRecommendation(BaseModel):
    """Structured output from the router."""

    action: str = Field(description="re-route | expedite | claim | cancel | standard_recovery")
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str
    matched_clauses: list[RuleMatch]
    needs_human_review: bool


class RouterState(BaseModel):
    """LangGraph state schema for the disruption router."""

    messages: Annotated[list[Any], add_messages]
    event: DisruptionEvent | None = None
    candidate_action: str | None = None
    recommendation: RouteRecommendation | None = None
    human_decision: str | None = None
