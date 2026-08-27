from contextlib import suppress

from fastapi.testclient import TestClient

from router.api.main import app
from router.graph.graph import graph, judge_grounding
from router.schemas.state import DisruptionEvent, RouteRecommendation, RuleMatch
from router.tools.rulebook import load_rulebook, lookup_clauses

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rulebook_loads() -> None:
    rulebook = load_rulebook("data/rulebook.json")
    assert len(rulebook.clauses) >= 1
    assert len(rulebook.policies) == 6
    for clause in rulebook.clauses:
        assert clause.id
        assert clause.text
        assert clause.action
        assert clause.event_types
        assert clause.severities
        assert clause.policy_id.startswith("POL-")


def test_lookup_clauses_match() -> None:
    matches = lookup_clauses("canceled", "critical", path="data/rulebook.json")
    assert any(m.action == "escalate_human" for m in matches)


def test_lookup_clauses_empty() -> None:
    matches = lookup_clauses("alien_invasion", "low", path="data/rulebook.json")
    assert matches == []


def test_graph_routes_without_hitl() -> None:
    event = DisruptionEvent(
        shipment_id="S-001",
        event_type="delay",
        severity="low",
        description="Minor delay on standard shipment",
    )
    config = {"configurable": {"thread_id": event.shipment_id}}
    result = graph.invoke({"event": event.model_dump(), "messages": []}, config)
    recommendation = RouteRecommendation.model_validate(result["recommendation"])
    assert recommendation.action == "monitor"
    assert recommendation.confidence >= 0.7


def test_judge_grounding_rejects_bogus_clause() -> None:
    event = DisruptionEvent(
        shipment_id="S-002",
        event_type="delay",
        severity="low",
        description="Minor delay",
    )
    bad_rec = RouteRecommendation(
        action="monitor",
        confidence=0.9,
        justification="Bogus justification.",
        matched_clauses=[
            RuleMatch(
                clause_id="C-999",
                clause_text="Nonexistent clause.",
                action="monitor",
                confidence="high",
                reason="None",
            )
        ],
        needs_human_review=False,
    )
    state = type("State", (), {"event": event, "recommendation": bad_rec})()
    result = judge_grounding(state)
    assert result["grounding_passed"] is False
    assert "C-999" in result["grounding_feedback"]


def test_review_queue_lists_and_resumes() -> None:
    thread_id = "S-REVIEW-001"
    event = DisruptionEvent(
        shipment_id=thread_id,
        event_type="canceled",
        severity="critical",
        description="Order canceled",
    )
    # Trigger an interrupt for a critical cancellation.
    config = {"configurable": {"thread_id": thread_id}}
    with suppress(Exception):
        graph.invoke({"event": event.model_dump(), "messages": []}, config)

    response = client.get("/reviews")
    assert response.status_code == 200
    reviews = response.json()
    assert any(r["thread_id"] == thread_id for r in reviews)

    resume = client.post(f"/reviews/{thread_id}", json={"decision": "approve"})
    assert resume.status_code == 200
    assert resume.json()["thread_id"] == thread_id
