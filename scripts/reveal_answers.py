#!/usr/bin/env python3
"""Reveal answers for weeks whose reveal_date has passed.

Regenerates answer.json and scoring_rubric.json using the same seed,
guaranteeing identical results due to deterministic generation.

Usage:
    python scripts/reveal_answers.py
    python scripts/reveal_answers.py --week 1  # force specific week
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finops_sim.catalog.loader import get_scenario
from finops_sim.catalog.selector import select_scenarios
from finops_sim.company.profile import generate_company_profile
from finops_sim.generators.answer import AnswerGenerator
from finops_sim.generators.base import GenerationContext
from finops_sim.generators.terraform import TerraformGenerator


def compute_seed(username: str, week: int, salt: str) -> int:
    data = f"{username}:{week}:{salt}"
    h = hashlib.sha256(data.encode()).hexdigest()
    return int(h, 16) % (2**31)


def load_members(config_dir: Path) -> list[str]:
    members_file = config_dir / "members.yaml"
    with open(members_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [m["username"] for m in data["members"]]


def find_weeks_to_reveal(config_dir: Path, force_week: int | None = None) -> list[dict]:
    """Find weeks whose reveal_date <= today."""
    weeks_dir = config_dir / "weeks"
    today = date.today()
    result = []

    for week_file in sorted(weeks_dir.glob("week-*.yaml")):
        with open(week_file, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        if force_week is not None and cfg["week"] != force_week:
            continue

        reveal_date_str = cfg.get("reveal_date")
        if not reveal_date_str:
            continue

        reveal_date = date.fromisoformat(str(reveal_date_str))
        if force_week is not None or reveal_date <= today:
            result.append(cfg)

    return result


def generate_answers_for_member(
    username: str,
    week: int,
    level: str,
    num_problems: int,
    category: str | None,
    salt: str,
    answers_dir: Path,
) -> list[str]:
    """Regenerate answers for a member using the same seed."""
    seed = compute_seed(username, week, salt)
    company = generate_company_profile(seed)
    scenarios = select_scenarios(level, num_problems, seed, category)

    generated = []
    for i, scenario_def in enumerate(scenarios):
        sub_seed = seed + i * 1000
        scenario = get_scenario(scenario_def.id)
        out_dir = answers_dir / f"week-{week:02d}" / username / scenario.id

        ctx = GenerationContext(
            scenario=scenario,
            seed=sub_seed,
            output_dir=str(out_dir),
            company_name=company.name,
            company_industry=company.industry,
        )

        # Build manifest to get resource names (needed for affected_resources)
        tf_gen = TerraformGenerator(ctx)
        tf_gen.build_manifest()

        # Generate answer and rubric
        answer_gen = AnswerGenerator(ctx)
        answer_gen.write(out_dir)

        generated.append(scenario.id)

    return generated


def main():
    parser = argparse.ArgumentParser(description="Reveal answers for due weeks")
    parser.add_argument("--week", type=int, default=None, help="Force specific week")
    parser.add_argument(
        "--salt",
        type=str,
        default=os.environ.get("GROUP_SALT", "default-dev-salt"),
    )
    parser.add_argument(
        "--config-dir", type=str, default=str(ROOT / "config"),
    )
    parser.add_argument(
        "--output", type=str, default=str(ROOT / "answers"),
    )
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    answers_dir = Path(args.output)
    members = load_members(config_dir)
    weeks = find_weeks_to_reveal(config_dir, args.week)

    if not weeks:
        print("No weeks ready to reveal.")
        return

    for week_cfg in weeks:
        week = week_cfg["week"]
        level = week_cfg["level"]
        num_problems = week_cfg.get("num_problems", 3)
        category = week_cfg.get("category")

        print(f"=== Revealing Week {week} answers ===")

        # Check if already revealed
        week_dir = answers_dir / f"week-{week:02d}"
        if week_dir.exists() and any(week_dir.iterdir()):
            print(f"  Already revealed, skipping.")
            continue

        for username in members:
            generated = generate_answers_for_member(
                username, week, level, num_problems, category, args.salt, answers_dir,
            )
            print(f"  {username}: {', '.join(generated)}")

    print("\nDone!")


if __name__ == "__main__":
    main()
