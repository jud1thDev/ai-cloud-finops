#!/usr/bin/env python3
"""Generate weekly problems for all members.

Usage:
    python scripts/generate_week.py --week 1 --level L1 --num-problems 3
    python scripts/generate_week.py --week 1  # reads from config/weeks/week-NN.yaml
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Set

import yaml

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from finops_sim.generators.orchestrator import _generate_one
from finops_sim.catalog.selector import select_scenarios
from finops_sim.company.profile import generate_company_profile


def compute_seed(username: str, week: int, salt: str) -> int:
    """Compute deterministic seed: sha256(username:week:salt) % 2^31."""
    data = f"{username}:{week}:{salt}"
    h = hashlib.sha256(data.encode()).hexdigest()
    return int(h, 16) % (2**31)


def load_members(config_dir: Path) -> list[str]:
    """Load member usernames from config/members.yaml."""
    members_file = config_dir / "members.yaml"
    with open(members_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [m["username"] for m in data["members"]]


def load_week_config(config_dir: Path, week: int) -> dict:
    """Load week config from config/weeks/week-NN.yaml."""
    week_file = config_dir / "weeks" / f"week-{week:02d}.yaml"
    if not week_file.exists():
        return {}
    with open(week_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_generators(week_config: dict) -> Set[str] | None:
    """Parse generators list from week config. Returns None if not specified."""
    gen_list = week_config.get("generators")
    if not gen_list:
        return None

    # Map shorthand names to generator names
    name_map = {
        "tf": None,  # always active, not an optional generator
        "metrics": None,
        "cost_report": None,
        "business_metrics": "business_metrics",
        "tags_inventory": "tags_inventory",
        "cloudwatch_format": "cloudwatch_format",
        "cur_report": "cur_report",
        "ri_sp_coverage": "ri_sp_coverage",
    }

    result = set()
    for name in gen_list:
        mapped = name_map.get(name, name)
        if mapped is not None:
            result.add(mapped)
    return result if result else None


def generate_for_member(
    username: str,
    week: int,
    level: str,
    num_problems: int,
    category: Optional[str],
    salt: str,
    output_base: Path,
    problems_only: bool = True,
    generators_override: Set[str] | None = None,
) -> list[dict]:
    """Generate problems for a single member."""
    seed = compute_seed(username, week, salt)
    member_dir = output_base / f"week-{week:02d}" / username

    # Use generate_auto logic but with member-specific seed
    company = generate_company_profile(seed)
    scenarios = select_scenarios(level, num_problems, seed, category)

    results = []
    for i, scenario in enumerate(scenarios):
        sub_seed = seed + i * 1000
        scenario_dir = member_dir / scenario.id
        result = _generate_one(
            scenario.id, scenario_dir, sub_seed, company,
            generators_override=generators_override,
        )
        results.append(result)

        if problems_only:
            # Remove answer files (they'll be generated at reveal time)
            answer_file = scenario_dir / "answer.json"
            rubric_file = scenario_dir / "scoring_rubric.json"
            if answer_file.exists():
                answer_file.unlink()
            if rubric_file.exists():
                rubric_file.unlink()

    # Write assignment manifest (which scenarios each member got)
    manifest = {
        "username": username,
        "week": week,
        "level": level,
        "seed": seed,
        "scenarios": [s.id for s in scenarios],
        "company": company.name,
    }
    if generators_override:
        manifest["active_generators"] = sorted(generators_override)

    manifest_path = member_dir / "assignment.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate weekly FinOps problems")
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument("--level", type=str, help="Problem level (L1/L2/L3)")
    parser.add_argument("--num-problems", type=int, help="Number of problems per member")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument(
        "--salt",
        type=str,
        default=os.environ.get("GROUP_SALT", "default-dev-salt"),
        help="Group salt for seed (default: GROUP_SALT env var)",
    )
    parser.add_argument(
        "--output", type=str, default=str(ROOT / "problems"),
        help="Output base directory",
    )
    parser.add_argument(
        "--config-dir", type=str, default=str(ROOT / "config"),
        help="Config directory",
    )
    args = parser.parse_args()

    config_dir = Path(args.config_dir)

    # Load week config as defaults (CLI args override)
    week_config = load_week_config(config_dir, args.week)
    level = args.level or week_config.get("level", "L1")
    num_problems = args.num_problems or week_config.get("num_problems", 3)
    category = args.category or week_config.get("category")
    generators_override = _parse_generators(week_config)

    members = load_members(config_dir)
    output_base = Path(args.output)

    print(f"=== Week {args.week} Generation ===")
    print(f"Level: {level}, Problems: {num_problems}, Category: {category or 'all'}")
    if generators_override:
        print(f"Generators: {', '.join(sorted(generators_override))}")
    print(f"Members: {', '.join(members)}")
    print(f"Salt: {'[from env]' if 'GROUP_SALT' in os.environ else '[default dev]'}")
    print()

    all_results = {}
    for username in members:
        print(f"Generating for {username}...")
        results = generate_for_member(
            username=username,
            week=args.week,
            level=level,
            num_problems=num_problems,
            category=category,
            salt=args.salt,
            output_base=output_base,
            generators_override=generators_override,
        )
        all_results[username] = results
        scenarios = [r["scenario_id"] for r in results]
        print(f"  -> {len(results)} problems: {', '.join(scenarios)}")

    print(f"\nDone! Problems written to {output_base}/week-{args.week:02d}/")


if __name__ == "__main__":
    main()
