"""Layer 1 canonical evaluation harness for the disruption router."""

import json
from datetime import UTC, datetime
from pathlib import Path

from router.graph.graph import graph
from router.schemas.state import RouteRecommendation

from .scenarios import SCENARIOS

RESULTS_DIR = Path("evals/.results")


def run() -> dict:
    """Run every canonical scenario and return a scored report."""
    results: list[dict] = []
    correct = 0
    for scenario in SCENARIOS:
        config = {"configurable": {"thread_id": scenario.event.shipment_id}}
        output = graph.invoke(
            {"event": scenario.event.model_dump(), "messages": []},
            config,
        )
        recommendation = RouteRecommendation.model_validate(output["recommendation"])
        passed = recommendation.action == scenario.expected_action
        if passed:
            correct += 1
        results.append(
            {
                "id": scenario.id,
                "expected": scenario.expected_action,
                "actual": recommendation.action,
                "passed": passed,
                "matched_clauses": [m.clause_id for m in recommendation.matched_clauses],
                "notes": scenario.notes,
            }
        )

    total = len(SCENARIOS)
    accuracy = correct / total if total else 0.0
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "results": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "layer1.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    report = run()
    print(f"Layer 1 eval: {report['correct']}/{report['total']} correct ({report['accuracy']:.1%})")
    for r in report["results"]:
        status = "✓" if r["passed"] else "✗"
        print(f"  {status} {r['id']}: expected={r['expected']} actual={r['actual']}")
    if report["accuracy"] < 0.85:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
