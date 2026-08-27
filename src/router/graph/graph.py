import sqlite3
from pathlib import Path
from typing import Any, cast

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from router.graph.llm import get_llm
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
    _ = lookup_clauses(event.event_type, event.severity, event=event)
    return {"candidate_action": None}


def _deterministic_route(event: Any, matches: list[Any]) -> RouteRecommendation:
    """Fallback router when LLM is unavailable.

    Selects the action from the highest-priority matched clause. If several
    clauses share the top priority, uses a simple majority vote among them.
    """
    if not matches:
        return RouteRecommendation(
            action="monitor",
            confidence=0.5,
            justification="No specific clause matched; falling back to monitor.",
            matched_clauses=[],
            needs_human_review=True,
        )

    top_priority = max(m.priority for m in matches)
    top_matches = [m for m in matches if m.priority == top_priority]
    actions = [m.action for m in top_matches]
    chosen_action = max(set(actions), key=actions.count)
    confidence = 0.9 if event.severity == "critical" else 0.75
    needs_review = event.severity in {"high", "critical"} or confidence < 0.8

    return RouteRecommendation(
        action=chosen_action,
        confidence=confidence,
        justification=f"Selected {chosen_action} from highest-priority clauses.",
        matched_clauses=matches,
        needs_human_review=needs_review,
    )


def route(state: RouterState) -> dict[str, Any]:
    """Generate a structured route recommendation from matched clauses.

    Uses an LLM with structured output when an API key is available; otherwise
    falls back to a deterministic majority vote over matched clauses.
    """
    event = state.event
    if event is None:
        raise ValueError("No disruption event in state")

    matches = lookup_clauses(event.event_type, event.severity, event=event)
    llm = get_llm()

    if llm is None:
        return {
            "recommendation": _deterministic_route(event, matches),
            "iteration": state.iteration + 1,
        }

    system_prompt = (
        "You are a logistics exception router. Given a disruption event and a "
        "set of matched policy clauses, emit a structured route recommendation. "
        "You must choose an action that is supported by at least one matched "
        "clause. Cite only clause IDs that appear in the matched clauses. "
        "Actions allowed: monitor, reroute, expedite, escalate_human, hold, cancel."
    )

    human_prompt = f"""Event:
- shipment_id: {event.shipment_id}
- event_type: {event.event_type}
- severity: {event.severity}
- description: {event.description}
- customer_tier: {event.customer_tier or "unknown"}

Matched clauses:
{[m.model_dump() for m in matches]}

Previous grounding feedback (if any): {state.grounding_feedback or "none"}
Iteration: {state.iteration + 1} / {state.max_iterations}
"""

    try:
        structured = llm.with_structured_output(RouteRecommendation)
        recommendation = cast(
            RouteRecommendation,
            structured.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt},
                ]
            ),
        )
        recommendation.matched_clauses = matches
    except Exception:
        # Any LLM failure should not block the route; fall back to deterministic.
        recommendation = _deterministic_route(event, matches)

    return {
        "recommendation": recommendation,
        "iteration": state.iteration + 1,
        "grounding_passed": False,
        "grounding_feedback": "",
    }


def judge_grounding(state: RouterState) -> dict[str, Any]:
    """Check that the recommendation is grounded in retrieved clauses."""
    event = state.event
    rec = state.recommendation
    if event is None or rec is None:
        return {
            "grounding_passed": False,
            "grounding_feedback": "Missing event or recommendation",
        }

    matches = lookup_clauses(event.event_type, event.severity, event=event)
    matched_ids = {m.clause_id for m in matches}
    cited_ids = {m.clause_id for m in rec.matched_clauses}

    errors: list[str] = []
    if not rec.matched_clauses:
        errors.append("Recommendation must cite at least one matched clause.")
    elif not cited_ids.issubset(matched_ids):
        errors.append(f"Cited clauses {cited_ids - matched_ids} are not in the retrieved set.")

    supported_actions = {m.action for m in matches}
    if rec.action not in supported_actions and supported_actions:
        errors.append(
            f"Action '{rec.action}' is not supported by any matched clause ({supported_actions})."
        )

    if rec.confidence < 0.0 or rec.confidence > 1.0:
        errors.append("Confidence must be between 0 and 1.")

    if errors:
        return {
            "grounding_passed": False,
            "grounding_feedback": "; ".join(errors),
        }

    return {
        "grounding_passed": True,
        "grounding_feedback": "All cited clauses support the recommended action.",
    }


def human_review(state: RouterState) -> dict[str, Any]:
    """Interrupt for human approval on high-stakes or low-confidence routes."""
    rec = state.recommendation
    if rec is None:
        raise ValueError("No recommendation in state")

    options = [
        "approve",
        "override_monitor",
        "override_reroute",
        "override_expedite",
        "override_escalate_human",
        "override_hold",
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
    decision = state.human_decision or (rec.action if rec else "monitor")
    return {"messages": [{"role": "assistant", "content": f"Final action: {decision}"}]}


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
def after_judge(state: RouterState) -> str:
    if state.grounding_passed:
        rec = state.recommendation
        if rec is not None and rec.needs_human_review:
            return "human_review"
        return "publish"
    if state.iteration >= state.max_iterations:
        return "publish"
    return "route"


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
    builder.add_node("judge_grounding", judge_grounding)
    builder.add_node("human_review", human_review)
    builder.add_node("publish", publish)

    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "retrieve")
    builder.add_edge("retrieve", "route")
    builder.add_edge("route", "judge_grounding")
    builder.add_conditional_edges("judge_grounding", after_judge)
    builder.add_edge("human_review", "publish")
    builder.add_edge("publish", END)

    conn = sqlite3.connect(path, check_same_thread=False)
    saver = SqliteSaver(conn)
    return builder.compile(checkpointer=saver)


graph = make_graph()
