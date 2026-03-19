#!/usr/bin/env python3
"""Score submissions against revealed answers.

Supports two formats:
1. New structured format (analysis key) → composite scorer
2. Legacy format (problem_identification key) → keyword matching

Usage:
    python scripts/score_submissions.py --week 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLATFORM_DIR = Path(__file__).resolve().parent.parent
ROOT = PLATFORM_DIR.parent
sys.path.insert(0, str(PLATFORM_DIR / "src"))


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r"\s+", " ", str(text).lower().strip())


def keyword_score(submission_text: str, reference_text: str, keywords: list[str]) -> float:
    """Score based on keyword presence (0.0 - 1.0)."""
    if not keywords:
        return 0.0
    sub = normalize(submission_text)
    matched = sum(1 for kw in keywords if normalize(kw) in sub)
    return matched / len(keywords)


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from reference answer text."""
    text = normalize(text)
    # Remove common stop words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "have", "has", "had", "do", "does", "did", "will", "would",
                  "could", "should", "may", "might", "can", "to", "of", "in",
                  "for", "on", "with", "at", "by", "from", "as", "or", "and",
                  "but", "not", "this", "that", "it", "its", "they", "them",
                  "는", "은", "이", "가", "를", "을", "의", "에", "에서", "로",
                  "으로", "와", "과", "도", "만", "다", "한", "된", "하는", "있는"}
    words = text.split()
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    # Return unique keywords
    return list(dict.fromkeys(keywords))


def score_submission_legacy(submission: dict, answer: dict, rubric: dict) -> dict:
    """Score a single submission using legacy keyword matching."""
    total_points = rubric.get("total_points", 100)
    rubric_items = rubric.get("rubric", {})

    scores = {}

    # 1. Problem Identification (30 pts default)
    item = rubric_items.get("identify_problem", {})
    max_pts = item.get("points", 30)
    ref_text = answer.get("problem_summary", "")
    sub_text = submission.get("problem_identification", "")
    keywords = extract_keywords(ref_text)
    ratio = keyword_score(sub_text, ref_text, keywords[:10])
    scores["identify_problem"] = round(max_pts * ratio, 1)

    # 2. Root Cause (20 pts default)
    item = rubric_items.get("identify_root_cause", {})
    max_pts = item.get("points", 20)
    ref_text = answer.get("root_cause", "")
    sub_text = submission.get("root_cause", "")
    keywords = extract_keywords(ref_text)
    ratio = keyword_score(sub_text, ref_text, keywords[:10])
    scores["identify_root_cause"] = round(max_pts * ratio, 1)

    # 3. Proposed Solution (30 pts default)
    item = rubric_items.get("propose_solution", {})
    max_pts = item.get("points", 30)
    ref_text = answer.get("recommendation", "")
    sub_text = submission.get("proposed_solution", "")
    keywords = extract_keywords(ref_text)
    ratio = keyword_score(sub_text, ref_text, keywords[:10])
    scores["propose_solution"] = round(max_pts * ratio, 1)

    # 4. Savings Estimate (20 pts default)
    item = rubric_items.get("estimate_savings", {})
    max_pts = item.get("points", 20)
    ref_monthly = answer.get("savings_estimate", {}).get("monthly_usd", 0)
    sub_savings = submission.get("estimated_savings_usd", 0)
    try:
        sub_savings = float(sub_savings)
    except (ValueError, TypeError):
        sub_savings = 0

    if ref_monthly > 0 and sub_savings > 0:
        ratio = min(sub_savings, ref_monthly) / max(sub_savings, ref_monthly)
        # Full marks if within 30%, partial otherwise
        if ratio >= 0.7:
            scores["estimate_savings"] = max_pts
        elif ratio >= 0.4:
            scores["estimate_savings"] = round(max_pts * 0.5, 1)
        else:
            scores["estimate_savings"] = round(max_pts * 0.2, 1)
    else:
        scores["estimate_savings"] = 0

    total = sum(scores.values())
    return {
        "scores": scores,
        "total": round(total, 1),
        "max_total": total_points,
        "percentage": round(total / total_points * 100, 1) if total_points > 0 else 0,
    }


def score_submission_structured(submission: dict, answer: dict, level: str = "L1",
                                business_metrics: dict | None = None) -> dict:
    """Score using the new composite scorer."""
    from finops_sim.scoring.composite import score_submission
    return score_submission(submission, answer, level, business_metrics)


def score_submission(submission: dict, answer: dict, rubric: dict,
                     level: str = "L1", business_metrics: dict | None = None) -> dict:
    """Route to appropriate scorer based on submission format."""
    if "analysis" in submission:
        return score_submission_structured(submission, answer, level, business_metrics)
    return score_submission_legacy(submission, answer, rubric)


def main():
    parser = argparse.ArgumentParser(description="Score submissions for a week")
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument(
        "--members-dir", type=str, default=str(ROOT / "members"),
    )
    parser.add_argument(
        "--output", type=str, default=str(ROOT / "scores"),
    )
    args = parser.parse_args()

    week_str = f"week-{args.week:02d}"
    members_dir = Path(args.members_dir)
    scores_dir = Path(args.output) / week_str

    if not members_dir.exists():
        print(f"No members directory found")
        sys.exit(0)

    scores_dir.mkdir(parents=True, exist_ok=True)
    summary = {"week": args.week, "members": {}}

    # Iterate over member directories
    for member_dir in sorted(members_dir.iterdir()):
        if not member_dir.is_dir() or member_dir.name.startswith('_'):
            continue

        username = member_dir.name
        sub_dir = member_dir / "submissions" / week_str
        answer_base = member_dir / "problems" / week_str

        if not sub_dir.exists():
            continue

        member_scores = {"username": username, "scenarios": {}, "total": 0, "max_total": 0}

        for sub_file in sorted(sub_dir.glob("*.json")):
            scenario_id = sub_file.stem
            submission = json.loads(sub_file.read_text(encoding="utf-8"))

            # Load corresponding answer and rubric
            answer_file = answer_base / scenario_id / "answer.json"
            rubric_file = answer_base / scenario_id / "scoring_rubric.json"

            if not answer_file.exists():
                print(f"  Warning: No answer for {username}/{scenario_id}")
                continue

            answer = json.loads(answer_file.read_text(encoding="utf-8"))
            rubric = json.loads(rubric_file.read_text(encoding="utf-8")) if rubric_file.exists() else {}

            # Check for business metrics
            bm_file = answer_base / scenario_id / "business_metrics.json"
            bm = json.loads(bm_file.read_text(encoding="utf-8")) if bm_file.exists() else None

            level = answer.get("level", "L1")
            result = score_submission(submission, answer, rubric, level, bm)
            member_scores["scenarios"][scenario_id] = result

            result_total = result.get("total", 0)
            result_max = result.get("max_total", result.get("total_max", 100))
            member_scores["total"] += result_total
            member_scores["max_total"] += result_max

        if member_scores["max_total"] > 0:
            member_scores["percentage"] = round(
                member_scores["total"] / member_scores["max_total"] * 100, 1
            )
        else:
            member_scores["percentage"] = 0

        # Write individual score file
        score_file = scores_dir / f"{username}.json"
        score_file.write_text(
            json.dumps(member_scores, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  {username}: {member_scores['total']}/{member_scores['max_total']} ({member_scores['percentage']}%)")

        summary["members"][username] = {
            "total": member_scores["total"],
            "max_total": member_scores["max_total"],
            "percentage": member_scores["percentage"],
        }

    # Write summary (leaderboard)
    ranked = sorted(
        summary["members"].items(),
        key=lambda x: x[1]["percentage"],
        reverse=True,
    )
    summary["leaderboard"] = [
        {"rank": i + 1, "username": name, **data}
        for i, (name, data) in enumerate(ranked)
    ]

    summary_file = scores_dir / "summary.json"
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nSummary written to {summary_file}")


if __name__ == "__main__":
    main()
