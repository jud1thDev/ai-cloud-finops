#!/usr/bin/env python3
"""Parse a GitHub Issue submission into a JSON file.

Called by the process-submission workflow when an issue with
the 'submission' label is created.

Usage:
    python scripts/parse_submission.py --issue-number 42 --issue-body "..." --issue-author alice
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_submission_body(body: str) -> dict:
    """Parse structured issue body into submission dict.

    Expected format (from issue template):
    ### Week
    1

    ### Scenario ID
    L1-003

    ### Problem Identification
    The issue is...

    ### Root Cause
    Because...

    ### Proposed Solution
    We should...

    ### Estimated Monthly Savings (USD)
    150
    """
    sections = {}
    current_key = None
    current_lines = []

    for line in body.split("\n"):
        header_match = re.match(r"^###\s+(.+)$", line.strip())
        if header_match:
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = header_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines).strip()

    # Normalize keys
    key_map = {
        "Week": "week",
        "Scenario ID": "scenario_id",
        "Problem Identification": "problem_identification",
        "Root Cause": "root_cause",
        "Proposed Solution": "proposed_solution",
        "Estimated Monthly Savings (USD)": "estimated_savings_usd",
        "Optimized Terraform": "optimized_terraform",
        "Attached Reports": "attached_reports",
    }

    result = {}
    for display_key, json_key in key_map.items():
        value = sections.get(display_key, "")
        # Try to parse numeric fields
        if json_key in ("week", "estimated_savings_usd"):
            try:
                value = float(value) if "." in str(value) else int(value)
            except (ValueError, TypeError):
                pass
        # Strip code fences from terraform
        if json_key == "optimized_terraform" and value:
            value = re.sub(r"^```\w*\n?", "", value)
            value = re.sub(r"\n?```$", "", value)
            value = value.strip()
        result[json_key] = value

    return result


def main():
    parser = argparse.ArgumentParser(description="Parse GitHub Issue submission")
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--issue-body", type=str, required=True)
    parser.add_argument("--issue-author", type=str, required=True)
    parser.add_argument(
        "--output", type=str, default=str(ROOT / "submissions"),
    )
    args = parser.parse_args()

    submission = parse_submission_body(args.issue_body)
    submission["author"] = args.issue_author
    submission["issue_number"] = args.issue_number
    submission["submitted_at"] = datetime.now(timezone.utc).isoformat()

    week = submission.get("week", "unknown")
    scenario_id = submission.get("scenario_id", "unknown")

    # Write to submissions/week-NN/username/SCENARIO_ID.json
    out_dir = Path(args.output) / f"week-{int(week):02d}" / args.issue_author
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{scenario_id}.json"

    out_file.write_text(
        json.dumps(submission, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Save terraform code as separate file if present
    tf_code = submission.get("optimized_terraform", "")
    if tf_code:
        tf_dir = out_dir / scenario_id
        tf_dir.mkdir(parents=True, exist_ok=True)
        tf_file = tf_dir / "solution.tf"
        tf_file.write_text(tf_code + "\n", encoding="utf-8")
        print(f"  Terraform saved: {tf_file}")

    print(f"Submission saved: {out_file}")
    print(f"  Author: {args.issue_author}")
    print(f"  Week: {week}, Scenario: {scenario_id}")


if __name__ == "__main__":
    main()
