"""Score unit economics calculation accuracy (15 points, L2+)."""

from __future__ import annotations

from typing import Any, Dict


def score(
    submission: Dict[str, Any],
    business_metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Score unit economics analysis. Max 15 points.

    Checks:
    - 5 points: unit_economics section present with all fields
    - 5 points: cost_per_order within reasonable range
    - 5 points: trend direction identified
    """
    ue = submission.get("analysis", {}).get("unit_economics")
    if not ue:
        return {"score": 0, "max": 15, "detail": "no unit_economics in submission"}

    total = 0
    details = []

    # Check 1: Required fields present
    required = ["cost_per_1k_requests", "cost_per_order", "trend", "vs_previous_period"]
    present = [f for f in required if f in ue]
    if len(present) == len(required):
        total += 5
        details.append("all fields present")
    else:
        missing = set(required) - set(present)
        total += round(5 * len(present) / len(required))
        details.append(f"missing: {missing}")

    # Check 2: Reasonable cost_per_order (if business_metrics available)
    if business_metrics and "current_unit_economics" in business_metrics:
        ref_cpo = business_metrics["current_unit_economics"].get("cost_per_order", 0)
        sub_cpo = ue.get("cost_per_order", 0)
        if ref_cpo > 0 and sub_cpo > 0:
            ratio = min(sub_cpo, ref_cpo) / max(sub_cpo, ref_cpo)
            if ratio >= 0.5:
                total += 5
                details.append("cost_per_order in range")
            else:
                total += 2
                details.append("cost_per_order out of range")
        else:
            total += 3  # Can't verify, partial credit
    else:
        # No reference data — give credit for having a value
        if ue.get("cost_per_order", 0) > 0:
            total += 3
            details.append("cost_per_order present (no ref to verify)")

    # Check 3: Trend direction
    if ue.get("trend") in ("improving", "stable", "degrading"):
        total += 5
        details.append(f"trend={ue['trend']}")
    else:
        details.append("invalid or missing trend")

    return {
        "score": min(total, 15),
        "max": 15,
        "detail": "; ".join(details),
    }
