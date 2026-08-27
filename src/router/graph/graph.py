import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from router.schemas.state import RouteRecommendation, RouterState
from router.settings import get_settings
from router.tools.rulebook import lookup_clauses


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def ingest(state: RouterState) -> dict[str, Any]:
    """Normalize incoming disruption event."""
    return {}


def retrieve(state: RouterState) -> dict[str, Any]:
    """Look up matching rulebook clauses for the reported event."""
    event = state.event
    if event is None:
        raise ValueError("No disruption event in state")
    _ = lookup_clauses(event.event_type, event.severity)
    return {"recommendation": None, "candidate_action": None}  # placeholder


def route(state: RouterState) -> dict[str, Any]:
    """Generate a structured route recommendation from matched clauses."""
    event = state.event
    if event is None:
        raise ValueError("No disruption event in state")

    matches = lookup_clauses(event.event_type, event.severity)
    if not matches:
        return {
            "recommendation": RouteRecommendation(
                action="standard_recovery",
                confidence=0.5,
                justification="No specific clause matched; falling back to standard recovery.",
                matched_clauses=[],
                needs_human_review=True,
            )
        }

    # Simple majority vote among matched clauses; LLM-based reasoning follows in Phase 2.
    actions = [m.action for m in matches]
    chosen_action = max(set(actions), key=actions.count)
    confidence = 0.9 if event.severity == "critical" else 0.75
    needs_review = event.severity in {"high", "critical"} or confidence < 0.8

    recommendation = RouteRecommendation(
        action=chosen_action,
        confidence=confidence,
        justification=f"Selected {chosen_action} based on {len(matches)} matched rulebook clauses.",
        matched_clauses=matches,
        needs_human_review=needs_review,
    )
    return {"recommendation": recommendation}


def human_review(state: RouterState) -> dict[str, Any]:
    """Interrupt for human approval on high-stakes or low-confidence routes."""
    rec = state.recommendation
    if rec is None:
        raise ValueError("No recommendation in state")

    options = [
        "approve",
        "override_standard_recovery",
        "override_expedite",
        "override_re_route",
        "override_claim",
        "override_cancel",
    ]
    decision = interrupt(
        {
            "shipment_id": state.event.shipment_id if state.event else "unknown",
            "recommended_action": rec.action,
            "confidence": rec.confidence,
            "justification": rec.justification,
            "matched_clauses": [m.model_dump() for m in rec.matched_clauses],
            "options": options,
        }
    )
    return {"human_decision": decision}


def publish(state: RouterState) -> dict[str, Any]:
    """Emit the final routed decision."""
    rec = state.recommendation
    decision = state.human_decision or (rec.action if rec else "standard_recovery")
    return {"messages": [{"role": "assistant", "content": f"Final action: {decision}"}]}


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
def needs_review(state: RouterState) -> str:
    rec = state.recommendation
    if rec is None:
        return "human_review"
    return "human_review" if rec.needs_human_review else "publish"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------
def make_graph(checkpoint_path: str | None = None) -> Any:
    """Build the compiled LangGraph with durable SQLite checkpointing."""
    settings = get_settings()
    path = checkpoint_path or settings.runs_db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    builder = StateGraph(RouterState)
    builder.add_node("ingest", ingest)
    builder.add_node("retrieve", retrieve)
    builder.add_node("route", route)
    builder.add_node("human_review", human_review)
    builder.add_node("publish", publish)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "retrieve")
    builder.add_edge("retrieve", "route")
    builder.add_conditional_edges("route", needs_review)
    builder.add_edge("human_review", "publish")
    builder.add_edge("publish", END)

    conn = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(conn)
    return builder.compile(checkpointer=saver)


graph = make_graph()
