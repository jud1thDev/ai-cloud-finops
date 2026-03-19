"""Score savings estimation accuracy (20 points)."""

from __future__ import annotations

from typing import Any, Dict


def score(submission: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
    """Score savings estimate. Max 20 points.

    Compares submission total_monthly_savings_usd vs answer savings_estimate.monthly_usd.
    ±30% → full marks, 30-60% off → half marks, >60% off → 4 points.
    """
    ref_monthly = answer.get("savings_estimate", {}).get("monthly_usd", 0)
    sub_savings = submission.get("summary", {}).get("total_monthly_savings_usd", 0)

    try:
        sub_savings = float(sub_savings)
    except (ValueError, TypeError):
        sub_savings = 0

    if ref_monthly <= 0:
        return {"score": 0, "max": 20, "detail": "no reference savings"}

    if sub_savings <= 0:
        return {"score": 0, "max": 20, "detail": "no savings estimate provided"}

    ratio = min(sub_savings, ref_monthly) / max(sub_savings, ref_monthly)

    if ratio >= 0.7:
        points = 20
        band = "within_30pct"
    elif ratio >= 0.4:
        points = 10
        band = "within_60pct"
    else:
        points = 4
        band = "over_60pct_off"

    return {
        "score": points,
        "max": 20,
        "accuracy_ratio": round(ratio, 3),
        "band": band,
        "submitted": sub_savings,
        "reference": ref_monthly,
    }
