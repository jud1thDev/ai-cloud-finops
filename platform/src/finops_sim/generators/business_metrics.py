"""Generate business metrics (daily traffic, unit economics) for L2+ scenarios."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import BUSINESS_METRICS_DAYS
from finops_sim.generators.base import GenerationContext
from finops_sim.utils.random_helpers import SeededRandom


class BusinessMetricsGenerator:
    """Generates 30-day daily business metrics and unit economics.

    Activated for L2+ scenarios. Traffic patterns are linked to the scenario's
    metrics_profile (e.g. spike scenarios get traffic spikes too).
    """

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed + 3000)

    def generate(self) -> Dict[str, Any]:
        scenario = self.ctx.scenario
        cost = scenario.cost_profile
        extras = getattr(scenario, "extras", {}) or {}
        metrics_profile_tag = extras.get("metrics_profile", "normal")

        # Base traffic parameters
        base_requests = self.rng.integer(50_000, 500_000)
        base_orders = int(base_requests * self.rng.floating(0.01, 0.05))
        base_data_gb = self.rng.floating(10.0, 200.0)

        daily_metrics: List[Dict[str, Any]] = []
        today = datetime(2026, 3, 18)
        start = today - timedelta(days=BUSINESS_METRICS_DAYS)

        for day in range(BUSINESS_METRICS_DAYS):
            date = start + timedelta(days=day)
            mult = self._traffic_multiplier(day, metrics_profile_tag)

            requests = int(base_requests * mult * self.rng.floating(0.9, 1.1))
            orders = int(base_orders * mult * self.rng.floating(0.85, 1.15))
            data_gb = round(base_data_gb * mult * self.rng.floating(0.9, 1.1), 2)

            daily_metrics.append({
                "date": date.strftime("%Y-%m-%d"),
                "requests": max(requests, 0),
                "orders": max(orders, 1),
                "data_processed_gb": max(data_gb, 0.1),
            })

        # Compute unit economics from cost report + traffic
        total_requests = sum(d["requests"] for d in daily_metrics)
        total_orders = sum(d["orders"] for d in daily_metrics)
        monthly_spend = cost.monthly_waste_usd * self.rng.floating(5.0, 15.0)

        cost_per_order = round(monthly_spend / max(total_orders, 1), 2)
        cost_per_1k_req = round(monthly_spend / max(total_requests / 1000, 1), 2)

        # Revenue estimate for cost_to_revenue_pct
        avg_order_value = self.rng.floating(15.0, 80.0)
        revenue = total_orders * avg_order_value
        cost_to_revenue = round(monthly_spend / max(revenue, 1) * 100, 2)

        return {
            "scenario_id": scenario.id,
            "period_days": BUSINESS_METRICS_DAYS,
            "daily_metrics": daily_metrics,
            "current_unit_economics": {
                "cost_per_order": cost_per_order,
                "cost_per_1k_requests": cost_per_1k_req,
                "cost_to_revenue_pct": min(cost_to_revenue, 100.0),
            },
        }

    def write(self, output_dir: Path) -> Path:
        data = self.generate()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "business_metrics.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out_path

    def _traffic_multiplier(self, day_index: int, profile: str) -> float:
        """Return a traffic multiplier based on the scenario's traffic profile."""
        if profile == "spike":
            # Spike in the middle of the period
            mid = BUSINESS_METRICS_DAYS // 2
            if abs(day_index - mid) <= 2:
                return self.rng.floating(2.5, 4.0)
            return 1.0

        if profile == "growth":
            # Linearly increasing traffic
            return 1.0 + (day_index / BUSINESS_METRICS_DAYS) * 0.5

        if profile == "declining":
            return 1.0 - (day_index / BUSINESS_METRICS_DAYS) * 0.4

        # "normal" — slight weekly pattern
        weekday = day_index % 7
        if weekday >= 5:  # weekend
            return self.rng.floating(0.6, 0.8)
        return 1.0
