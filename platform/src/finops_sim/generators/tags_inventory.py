"""Generate resource tag inventory for L2+ scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import STANDARD_TAGS
from finops_sim.generators.base import GenerationContext
from finops_sim.utils.random_helpers import SeededRandom


class TagsInventoryGenerator:
    """Generates per-resource tag audit.

    Problem resources have 20-40% tag compliance (missing standard tags).
    Decoy resources have full tag compliance.
    """

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed + 4000)

    def generate(self) -> Dict[str, Any]:
        manifest = self.ctx.manifest
        if not manifest:
            return {"resources": [], "summary": {}}

        resources_out: List[Dict[str, Any]] = []
        total_tags = 0
        total_possible = 0

        for inst in manifest.instances:
            if inst.is_problem:
                tags, missing = self._generate_problem_tags(inst)
            else:
                tags, missing = self._generate_compliant_tags(inst)

            total_tags += len(tags)
            total_possible += len(STANDARD_TAGS)

            resources_out.append({
                "resource_name": inst.resource_name,
                "resource_type": inst.resource_type,
                "is_problem": inst.is_problem,
                "tags": tags,
                "missing_tags": missing,
                "compliance_pct": round(
                    len(tags) / max(len(STANDARD_TAGS), 1) * 100, 1
                ),
            })

        coverage_pct = round(total_tags / max(total_possible, 1) * 100, 1)

        return {
            "scenario_id": self.ctx.scenario.id,
            "standard_tags": list(STANDARD_TAGS),
            "resources": resources_out,
            "summary": {
                "total_resources": len(resources_out),
                "tag_coverage_pct": coverage_pct,
                "fully_compliant": sum(
                    1 for r in resources_out if not r["missing_tags"]
                ),
                "non_compliant": sum(
                    1 for r in resources_out if r["missing_tags"]
                ),
            },
        }

    def write(self, output_dir: Path) -> Path:
        data = self.generate()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "tags_inventory.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out_path

    def _generate_problem_tags(self, inst) -> tuple[dict, list]:
        """Problem resources: 20-40% of standard tags present."""
        keep_ratio = self.rng.floating(0.2, 0.4)
        keep_count = max(1, int(len(STANDARD_TAGS) * keep_ratio))
        present_keys = list(self.rng.sample(list(STANDARD_TAGS), keep_count))
        tags = {k: self._tag_value(k, inst) for k in present_keys}
        missing = [k for k in STANDARD_TAGS if k not in tags]
        return tags, missing

    def _generate_compliant_tags(self, inst) -> tuple[dict, list]:
        """Decoy resources: full tag compliance."""
        tags = {k: self._tag_value(k, inst) for k in STANDARD_TAGS}
        return tags, []

    def _tag_value(self, key: str, inst) -> str:
        """Generate a realistic tag value."""
        values = {
            "Service": self.rng.choice([
                "api", "web", "worker", "data-pipeline", "auth", "search",
            ]),
            "Team": self.rng.choice([
                "platform", "backend", "infra", "data", "devops", "frontend",
            ]),
            "Env": self.rng.choice(["prod", "staging", "dev"]),
            "CostCenter": f"CC-{self.rng.integer(100, 999)}",
            "Owner": self.rng.choice([
                "alice@example.com", "bob@example.com",
                "charlie@example.com", "devops@example.com",
            ]),
        }
        return values.get(key, f"{key}-{inst.resource_name[:6]}")
