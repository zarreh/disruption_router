from fastapi.testclient import TestClient

from router.api.main import app
from router.graph.graph import graph
from router.schemas.state import DisruptionEvent, RouteRecommendation
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
