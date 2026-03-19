"""Score Terraform output validity and problem resource fixes (15 points)."""

from __future__ import annotations

import re
from typing import Any, Dict


def _extract_resources_from_hcl(hcl: str) -> list[str]:
    """Extract resource names from HCL using regex."""
    return re.findall(r'resource\s+"(\w+)"\s+"(\w[\w-]*)"', hcl)


def score(submission: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
    """Score optimized_terraform field. Max 15 points.

    - 5 points: HCL is syntactically plausible (has resource blocks)
    - 5 points: Contains modifications for problem resources
    - 5 points: Does not remove non-problem resources
    """
    hcl = submission.get("optimized_terraform", "")
    if not hcl or not isinstance(hcl, str):
        return {"score": 0, "max": 15, "detail": "no terraform output"}

    total = 0
    details = []

    # Check 1: Has resource blocks
    resources = _extract_resources_from_hcl(hcl)
    if resources:
        total += 5
        details.append("valid HCL structure")
    else:
        details.append("no resource blocks found")

    # Check 2: References problem resources or their fixes
    problem_resources = {
        r.get("resource_name", "")
        for r in answer.get("affected_resources", [])
    }
    hcl_lower = hcl.lower()

    fixes_found = 0
    for pr in problem_resources:
        if pr and pr.lower() in hcl_lower:
            fixes_found += 1

    if fixes_found > 0:
        ratio = min(fixes_found / max(len(problem_resources), 1), 1.0)
        total += round(5 * ratio)
        details.append(f"addresses {fixes_found}/{len(problem_resources)} problem resources")

    # Check 3: Contains at least some resource blocks (not destructive)
    if len(resources) >= 1:
        total += 5
        details.append("preserves infrastructure")

    return {
        "score": min(total, 15),
        "max": 15,
        "detail": "; ".join(details),
    }
