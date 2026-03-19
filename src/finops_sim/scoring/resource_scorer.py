"""Score problem resource identification accuracy (30 points).

Uses precision + recall against the answer's affected_resources.
"""

from __future__ import annotations

from typing import Any, Dict, Set


def _extract_resources(submission: Dict[str, Any]) -> Set[str]:
    """Extract resource names from submission's problems_found."""
    problems = submission.get("analysis", {}).get("problems_found", [])
    return {p.get("resource", "") for p in problems if p.get("resource")}


def _extract_answer_resources(answer: Dict[str, Any]) -> Set[str]:
    """Extract problem resource names from reference answer."""
    return {
        r.get("resource_name", "")
        for r in answer.get("affected_resources", [])
        if r.get("resource_name")
    }


def score(submission: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
    """Score resource identification. Max 30 points.

    15 points for precision, 15 points for recall.
    """
    found = _extract_resources(submission)
    expected = _extract_answer_resources(answer)

    if not expected:
        return {"score": 0, "max": 30, "detail": "no expected resources in answer"}

    if not found:
        return {"score": 0, "max": 30, "precision": 0, "recall": 0}

    true_positives = found & expected
    precision = len(true_positives) / len(found) if found else 0
    recall = len(true_positives) / len(expected) if expected else 0

    precision_score = round(15 * precision, 1)
    recall_score = round(15 * recall, 1)

    return {
        "score": round(precision_score + recall_score, 1),
        "max": 30,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "true_positives": sorted(true_positives),
        "false_positives": sorted(found - expected),
        "false_negatives": sorted(expected - found),
    }
