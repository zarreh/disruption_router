"""HITL review-queue endpoints."""

from typing import Any, cast

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from router.graph.graph import graph
from router.settings import get_settings

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _list_thread_ids() -> list[str]:
    """Return distinct thread IDs from the checkpoint store."""
    settings = get_settings()
    import sqlite3

    conn = sqlite3.connect(settings.runs_db_path, check_same_thread=False)
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def _extract_interrupt(snapshot: Any) -> dict[str, Any] | None:
    """Return the first pending interrupt payload from a state snapshot."""
    for task in getattr(snapshot, "tasks", ()):
        interrupts = getattr(task, "interrupts", ())
        if interrupts:
            return cast(dict[str, Any], interrupts[0].value)
    return None


class ReviewItem(BaseModel):
    thread_id: str
    shipment_id: str
    recommended_action: str
    confidence: float
    justification: str
    matched_clauses: list[dict[str, Any]]
    options: list[str]


class ReviewDecision(BaseModel):
    decision: str


@router.get("", response_model=list[ReviewItem])
def list_reviews() -> list[ReviewItem]:
    """List all threads currently awaiting human review."""
    items: list[ReviewItem] = []
    for thread_id in _list_thread_ids():
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = graph.get_state(config)
        interrupt = _extract_interrupt(snapshot)
        if interrupt is None:
            continue
        items.append(
            ReviewItem(
                thread_id=thread_id,
                shipment_id=interrupt.get("shipment_id", thread_id),
                recommended_action=interrupt.get("recommended_action", ""),
                confidence=interrupt.get("confidence", 0.0),
                justification=interrupt.get("justification", ""),
                matched_clauses=interrupt.get("matched_clauses", []),
                options=interrupt.get("options", []),
            )
        )
    return items


@router.post("/{thread_id}")
def submit_review(
    thread_id: str = Path(..., description="Thread ID of the interrupted run"),
    *,
    decision: ReviewDecision,
) -> dict[str, Any]:
    """Submit a human decision and resume the interrupted run."""
    from langgraph.types import Command

    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    if _extract_interrupt(snapshot) is None:
        raise HTTPException(status_code=404, detail="No pending review for this thread")

    result = graph.invoke(Command(resume=decision.decision), config)
    return {"thread_id": thread_id, "state": result}
