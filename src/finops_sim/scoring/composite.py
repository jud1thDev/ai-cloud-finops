"""Composite scorer: orchestrates all scoring dimensions with level-based weights."""

from __future__ import annotations

from typing import Any, Dict

from finops_sim.scoring import (
    alert_scorer,
    economics_scorer,
    resource_scorer,
    savings_scorer,
    schema_scorer,
    terraform_scorer,
)

# Default weights per level (scorer_name → weight multiplier)
# All scorers have a base max; weight scales contribution to final 100-point score.
LEVEL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "L1": {
        "schema": 1.0,
        "resource": 1.0,
        "savings": 1.0,
        "terraform": 1.0,
        "economics": 0.0,
        "alerts": 0.0,
    },
    "L2": {
        "schema": 1.0,
        "resource": 1.0,
        "savings": 1.0,
        "terraform": 1.0,
        "economics": 1.0,
        "alerts": 0.0,
    },
    "L3": {
        "schema": 1.0,
        "resource": 1.0,
        "savings": 1.0,
        "terraform": 1.0,
        "economics": 1.0,
        "alerts": 1.0,
    },
}


def score_submission(
    submission: Dict[str, Any],
    answer: Dict[str, Any],
    level: str = "L1",
    business_metrics: Dict[str, Any] | None = None,
    scoring_weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """Score a structured AI submission. Returns breakdown + total out of 100.

    Args:
        submission: The student AI's output (matching output_schema.json).
        answer: The reference answer.json for this scenario.
        level: Scenario level (L1/L2/L3).
        business_metrics: Optional business_metrics.json data for economics scoring.
        scoring_weights: Optional custom weight overrides.
    """
    weights = scoring_weights or LEVEL_WEIGHTS.get(level, LEVEL_WEIGHTS["L1"])

    results: Dict[str, Any] = {}

    # Schema validation (10 pts)
    if weights.get("schema", 0) > 0:
        results["schema"] = schema_scorer.score(submission, level)
    else:
        results["schema"] = {"score": 0, "max": 10, "detail": "skipped"}

    # Resource identification (30 pts)
    if weights.get("resource", 0) > 0:
        results["resource"] = resource_scorer.score(submission, answer)
    else:
        results["resource"] = {"score": 0, "max": 30, "detail": "skipped"}

    # Terraform quality (15 pts)
    if weights.get("terraform", 0) > 0:
        results["terraform"] = terraform_scorer.score(submission, answer)
    else:
        results["terraform"] = {"score": 0, "max": 15, "detail": "skipped"}

    # Savings estimation (20 pts)
    if weights.get("savings", 0) > 0:
        results["savings"] = savings_scorer.score(submission, answer)
    else:
        results["savings"] = {"score": 0, "max": 20, "detail": "skipped"}

    # Unit economics (15 pts, L2+)
    if weights.get("economics", 0) > 0:
        results["economics"] = economics_scorer.score(submission, business_metrics)
    else:
        results["economics"] = {"score": 0, "max": 15, "detail": "skipped"}

    # Alerts (10 pts, L3)
    if weights.get("alerts", 0) > 0:
        results["alerts"] = alert_scorer.score(submission)
    else:
        results["alerts"] = {"score": 0, "max": 10, "detail": "skipped"}

    # Compute totals
    total_score = sum(r["score"] for r in results.values())
    total_max = sum(
        r["max"] for name, r in results.items()
        if weights.get(name, 0) > 0
    )

    # Normalize to 100
    if total_max > 0:
        normalized = round(total_score / total_max * 100, 1)
    else:
        normalized = 0

    return {
        "total": round(total_score, 1),
        "total_max": total_max,
        "percentage": normalized,
        "level": level,
        "breakdown": results,
    }
