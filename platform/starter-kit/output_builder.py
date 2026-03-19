"""Build and validate the output JSON matching spec/output_schema.json."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def extract_json_from_response(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response text.

    LLMs often wrap JSON in ```json ... ``` blocks or add explanation text.
    This function extracts the first valid JSON object found.
    """
    # Try 1: Find ```json ... ``` block
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try 2: Find first { ... } block
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = -1

    raise ValueError("No valid JSON found in LLM response")


def build_output(
    problems: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    summary: Dict[str, Any],
    unit_economics: Optional[Dict[str, Any]] = None,
    elasticity: Optional[Dict[str, Any]] = None,
    alerts: Optional[List[Dict[str, Any]]] = None,
    optimized_terraform: Optional[str] = None,
) -> Dict[str, Any]:
    """Build output matching spec/output_schema.json."""
    analysis: Dict[str, Any] = {
        "problems_found": problems,
    }
    if unit_economics:
        analysis["unit_economics"] = unit_economics
    if elasticity:
        analysis["elasticity"] = elasticity

    output: Dict[str, Any] = {
        "analysis": analysis,
        "recommendations": recommendations,
        "summary": summary,
    }
    if alerts:
        output["alerts"] = alerts
    if optimized_terraform:
        output["optimized_terraform"] = optimized_terraform

    return output


def validate_output(output: Dict[str, Any], level: str = "L1") -> List[str]:
    """Validate output against schema. Returns list of error messages."""
    errors: List[str] = []

    # Check required top-level fields
    if "analysis" not in output:
        errors.append("missing: analysis")
    if "recommendations" not in output:
        errors.append("missing: recommendations")
    if "summary" not in output:
        errors.append("missing: summary")

    analysis = output.get("analysis", {})
    if "problems_found" not in analysis:
        errors.append("missing: analysis.problems_found")

    # Level-specific checks
    if level in ("L2", "L3") and "unit_economics" not in analysis:
        errors.append(f"missing for {level}: analysis.unit_economics")
    if level == "L3":
        if "elasticity" not in analysis:
            errors.append("missing for L3: analysis.elasticity")
        if "alerts" not in output:
            errors.append("missing for L3: alerts")

    # Validate problems_found structure
    for i, p in enumerate(analysis.get("problems_found", [])):
        for field in ["resource", "issue_type", "severity", "evidence", "recommendation", "estimated_savings"]:
            if field not in p:
                errors.append(f"problems_found[{i}]: missing {field}")

    # Validate summary
    summary = output.get("summary", {})
    for field in ["total_issues_found", "total_monthly_savings_usd", "confidence_score"]:
        if field not in summary:
            errors.append(f"summary: missing {field}")

    return errors


def save_output(output: Dict[str, Any], path: str = "analysis.json") -> Path:
    """Save output to JSON file."""
    p = Path(path)
    p.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p
