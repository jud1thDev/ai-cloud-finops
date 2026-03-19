"""Generate RI/SP (Reserved Instance / Savings Plan) coverage data for L3 scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.generators.base import GenerationContext
from finops_sim.utils.random_helpers import SeededRandom


class RISPCoverageGenerator:
    """Generates RI/SP coverage analysis.

    Activated only for 'rate' category scenarios or scenarios tagged 'ri-sp'.
    Shows current reservation coverage and potential savings from RI/SP adoption.
    """

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed + 7000)

    def generate(self) -> Dict[str, Any]:
        scenario = self.ctx.scenario
        cost = scenario.cost_profile
        monthly_spend = cost.monthly_waste_usd * self.rng.floating(5.0, 15.0)

        # Current coverage
        ri_coverage_pct = self.rng.floating(5.0, 25.0)
        sp_coverage_pct = self.rng.floating(0.0, 15.0)
        on_demand_pct = round(100.0 - ri_coverage_pct - sp_coverage_pct, 1)

        # Existing reservations
        reservations = self._generate_reservations()

        # Potential savings
        coverable_spend = monthly_spend * (on_demand_pct / 100)
        ri_savings_pct = self.rng.floating(0.30, 0.45)
        sp_savings_pct = self.rng.floating(0.20, 0.35)

        return {
            "scenario_id": scenario.id,
            "coverage_summary": {
                "ri_coverage_pct": round(ri_coverage_pct, 1),
                "sp_coverage_pct": round(sp_coverage_pct, 1),
                "on_demand_pct": round(on_demand_pct, 1),
                "total_monthly_compute_spend": round(monthly_spend, 2),
            },
            "reservations": reservations,
            "on_demand_spend_pct": round(on_demand_pct, 1),
            "potential_savings": {
                "with_1yr_ri": {
                    "savings_pct": round(ri_savings_pct * 100, 1),
                    "monthly_savings_usd": round(coverable_spend * ri_savings_pct, 2),
                },
                "with_1yr_sp": {
                    "savings_pct": round(sp_savings_pct * 100, 1),
                    "monthly_savings_usd": round(coverable_spend * sp_savings_pct, 2),
                },
                "with_3yr_ri": {
                    "savings_pct": round(ri_savings_pct * 1.4 * 100, 1),
                    "monthly_savings_usd": round(coverable_spend * ri_savings_pct * 1.4, 2),
                },
            },
        }

    def write(self, output_dir: Path) -> Path:
        data = self.generate()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "ri_sp_coverage.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out_path

    def _generate_reservations(self) -> List[Dict[str, Any]]:
        """Generate a small set of existing reservations."""
        count = self.rng.integer(1, 3)
        types = ["Standard RI", "Convertible RI", "Compute Savings Plan"]
        instance_types = ["m5.large", "r5.xlarge", "c5.2xlarge", "t3.medium"]
        terms = ["1yr", "3yr"]

        reservations = []
        for _ in range(count):
            reservations.append({
                "type": self.rng.choice(types),
                "instance_type": self.rng.choice(instance_types),
                "term": self.rng.choice(terms),
                "count": self.rng.integer(1, 5),
                "utilization_pct": round(self.rng.floating(60.0, 95.0), 1),
                "monthly_cost_usd": round(self.rng.floating(50.0, 500.0), 2),
            })
        return reservations
