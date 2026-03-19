"""Output schema validators — verify generated artifacts are well-formed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class ValidationError(Exception):
    """Raised when a generated artifact fails validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Validation failed:\n" + "\n".join("  - " + e for e in errors))


def validate_output_dir(output_dir: Path) -> List[str]:
    """Validate all artifacts in an output directory.

    Returns a list of error strings. Empty list means all valid.
    """
    errors: List[str] = []
    errors.extend(_check_main_tf(output_dir))
    errors.extend(_check_metrics(output_dir))
    errors.extend(_check_cost_report(output_dir))
    errors.extend(_check_answer(output_dir))
    errors.extend(_check_scoring_rubric(output_dir))
    errors.extend(_check_readme(output_dir))
    return errors


def _check_main_tf(d: Path) -> List[str]:
    errors: List[str] = []
    tf = d / "main.tf"
    if not tf.exists():
        errors.append("main.tf missing")
        return errors
    content = tf.read_text(encoding="utf-8")
    if 'provider "aws"' not in content:
        errors.append("main.tf: missing provider block")
    if "resource " not in content:
        errors.append("main.tf: no resource blocks found")
    return errors


def _check_json_file(d: Path, name: str, required_keys: List[str]) -> List[str]:
    errors: List[str] = []
    f = d / name
    if not f.exists():
        errors.append("%s missing" % name)
        return errors
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append("%s: invalid JSON — %s" % (name, e))
        return errors
    for key in required_keys:
        if key not in data:
            errors.append("%s: missing key '%s'" % (name, key))
    return errors


def _check_metrics(d: Path) -> List[str]:
    errors: List[str] = []
    f = d / "metrics" / "metrics.json"
    if not f.exists():
        errors.append("metrics/metrics.json missing")
        return errors
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append("metrics.json: invalid JSON — %s" % e)
        return errors

    if "metadata" not in data:
        errors.append("metrics.json: missing 'metadata'")
    else:
        meta = data["metadata"]
        for k in ("scenario_id", "period_days", "resolution", "points_per_series"):
            if k not in meta:
                errors.append("metrics.json metadata: missing '%s'" % k)

    if "resources" not in data:
        errors.append("metrics.json: missing 'resources'")
    elif len(data["resources"]) == 0:
        errors.append("metrics.json: no resources")
    else:
        for rname, rdata in data["resources"].items():
            if "metrics" not in rdata:
                errors.append("metrics.json resource '%s': missing 'metrics'" % rname)
            elif not rdata["metrics"]:
                errors.append("metrics.json resource '%s': empty metrics" % rname)
            else:
                for mname, mdata in rdata["metrics"].items():
                    if "datapoints" not in mdata:
                        errors.append(
                            "metrics.json %s.%s: missing 'datapoints'" % (rname, mname)
                        )
                    elif not isinstance(mdata["datapoints"], list):
                        errors.append(
                            "metrics.json %s.%s: datapoints not a list" % (rname, mname)
                        )
    return errors


def _check_cost_report(d: Path) -> List[str]:
    return _check_json_file(
        d,
        "cost_report.json",
        ["scenario_id", "currency", "period_months", "monthly_data", "summary"],
    )


def _check_answer(d: Path) -> List[str]:
    errors = _check_json_file(
        d,
        "answer.json",
        [
            "scenario_id",
            "severity",
            "problem_summary",
            "recommendation",
            "savings_estimate",
            "affected_resources",
            "evidence_pointers",
        ],
    )
    f = d / "answer.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sev = data.get("severity", "")
            if sev not in ("low", "medium", "high", "critical"):
                errors.append("answer.json: invalid severity '%s'" % sev)
            savings = data.get("savings_estimate", {})
            if "monthly_usd" not in savings:
                errors.append("answer.json: missing savings_estimate.monthly_usd")
            elif savings["monthly_usd"] <= 0:
                errors.append("answer.json: savings_estimate.monthly_usd must be > 0")
        except json.JSONDecodeError:
            pass  # already caught above
    return errors


def _check_scoring_rubric(d: Path) -> List[str]:
    errors = _check_json_file(
        d,
        "scoring_rubric.json",
        ["scenario_id", "total_points", "rubric"],
    )
    f = d / "scoring_rubric.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("total_points", 0) != 100:
                errors.append(
                    "scoring_rubric.json: total_points=%s, expected 100"
                    % data.get("total_points")
                )
        except json.JSONDecodeError:
            pass
    return errors


def _check_readme(d: Path) -> List[str]:
    errors: List[str] = []
    f = d / "README.md"
    if not f.exists():
        errors.append("README.md missing")
        return errors
    content = f.read_text(encoding="utf-8")
    if len(content) < 100:
        errors.append("README.md: suspiciously short (%d chars)" % len(content))
    return errors
