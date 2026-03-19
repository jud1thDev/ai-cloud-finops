"""Score alert generation quality (10 points, L3)."""

from __future__ import annotations

from typing import Any, Dict, List


def score(submission: Dict[str, Any]) -> Dict[str, Any]:
    """Score alerts section. Max 10 points.

    - 4 points: alerts array present and non-empty
    - 3 points: each alert has required fields (channel, urgency, title, message, severity)
    - 3 points: severity levels are appropriate (at least one warning/critical)
    """
    alerts: List[Dict[str, Any]] = submission.get("alerts", [])

    if not alerts:
        return {"score": 0, "max": 10, "detail": "no alerts provided"}

    total = 0
    details = []

    # Check 1: Non-empty
    total += 4
    details.append(f"{len(alerts)} alerts")

    # Check 2: Required fields
    required = {"channel", "urgency", "title", "message", "severity"}
    valid_count = 0
    for alert in alerts:
        if required.issubset(alert.keys()):
            valid_count += 1
    field_ratio = valid_count / len(alerts)
    total += round(3 * field_ratio)
    if field_ratio < 1.0:
        details.append(f"{valid_count}/{len(alerts)} properly structured")

    # Check 3: Severity appropriateness
    severities = {a.get("severity") for a in alerts}
    urgencies = {a.get("urgency") for a in alerts}
    has_actionable = bool(
        severities & {"high", "critical"} or urgencies & {"warning", "critical"}
    )
    if has_actionable:
        total += 3
        details.append("actionable severity present")
    else:
        total += 1
        details.append("only info/low severity")

    return {
        "score": min(total, 10),
        "max": 10,
        "detail": "; ".join(details),
    }
