"""Generate monthly cost history JSON for a scenario."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import COST_HISTORY_MONTHS
from finops_sim.generators.base import GenerationContext
from finops_sim.utils.random_helpers import SeededRandom


class CostReportGenerator:
    """Generates a 6-month cost history report showing the waste pattern."""

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed + 2000)

    def generate(self) -> Dict[str, Any]:
        scenario = self.ctx.scenario
        cost = scenario.cost_profile
        monthly_waste = cost.monthly_waste_usd

        # Base spend: waste is some fraction of total spend
        base_spend = monthly_waste * self.rng.floating(5.0, 15.0)

        months: List[Dict[str, Any]] = []
        for i in range(COST_HISTORY_MONTHS):
            month_offset = COST_HISTORY_MONTHS - 1 - i  # 0 = most recent
            # Add some variance to total spend
            total_noise = self.rng.floating(0.92, 1.08)
            total = round(base_spend * total_noise, 2)

            # Waste remains relatively constant (the problem persists)
            waste_noise = self.rng.floating(0.95, 1.05)
            waste = round(monthly_waste * waste_noise, 2)

            # Build per-service breakdown
            services_breakdown = self._build_service_breakdown(
                total, waste, cost.services_affected
            )

            months.append({
                "month_offset": month_offset,
                "label": "M-%d" % month_offset,
                "total_spend_usd": total,
                "waste_usd": waste,
                "waste_pct": round(waste / total * 100, 1) if total > 0 else 0,
                "services": services_breakdown,
            })

        return {
            "scenario_id": scenario.id,
            "currency": "USD",
            "period_months": COST_HISTORY_MONTHS,
            "monthly_data": months,
            "summary": {
                "avg_monthly_total": round(
                    sum(m["total_spend_usd"] for m in months) / len(months), 2
                ),
                "avg_monthly_waste": round(
                    sum(m["waste_usd"] for m in months) / len(months), 2
                ),
                "waste_services": cost.services_affected,
                "pricing_note": cost.pricing_note,
            },
        }

    def _build_service_breakdown(
        self,
        total: float,
        waste: float,
        waste_services: List[str],
    ) -> List[Dict[str, Any]]:
        """Build a per-service cost breakdown."""
        scenario = self.ctx.scenario
        all_services = list(set(scenario.aws_services + waste_services))

        breakdown: List[Dict[str, Any]] = []
        remaining = total

        # First allocate waste to affected services
        waste_per_svc = waste / max(len(waste_services), 1)
        for svc in waste_services:
            svc_total = waste_per_svc + self.rng.floating(0.0, waste_per_svc * 0.5)
            svc_total = min(round(svc_total, 2), remaining)
            remaining -= svc_total
            breakdown.append({
                "service": svc,
                "spend_usd": svc_total,
                "contains_waste": True,
            })

        # Distribute remaining among other services
        other_services = [s for s in all_services if s not in waste_services]
        if other_services and remaining > 0:
            shares = [self.rng.floating(0.5, 2.0) for _ in other_services]
            share_total = sum(shares)
            for svc, share in zip(other_services, shares):
                svc_spend = round(remaining * share / share_total, 2)
                breakdown.append({
                    "service": svc,
                    "spend_usd": svc_spend,
                    "contains_waste": False,
                })

        return breakdown

    def write(self, output_dir: Path) -> Path:
        data = self.generate()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "cost_report.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out_path
