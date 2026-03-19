"""Read and summarize problem files for LLM consumption."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, Optional


def read_problem(problem_dir: str) -> Dict[str, Any]:
    """Read all files from a problem directory and return structured data."""
    d = Path(problem_dir)
    if not d.exists():
        raise FileNotFoundError(f"Problem directory not found: {d}")

    result: Dict[str, Any] = {}

    # 1. main.tf (always present)
    tf_path = d / "main.tf"
    if tf_path.exists():
        result["terraform"] = tf_path.read_text(encoding="utf-8")

    # 2. metrics.json (always present)
    metrics_path = d / "metrics" / "metrics.json"
    if metrics_path.exists():
        raw = json.loads(metrics_path.read_text(encoding="utf-8"))
        result["metrics"] = summarize_metrics(raw)
        result["metrics_raw"] = raw

    # 3. cost_report.json (always present)
    cost_path = d / "cost_report.json"
    if cost_path.exists():
        result["cost_report"] = json.loads(cost_path.read_text(encoding="utf-8"))

    # 4. business_metrics.json (L2+)
    bm_path = d / "business_metrics.json"
    if bm_path.exists():
        result["business_metrics"] = json.loads(bm_path.read_text(encoding="utf-8"))

    # 5. tags_inventory.json (L2+)
    tags_path = d / "tags_inventory.json"
    if tags_path.exists():
        result["tags_inventory"] = json.loads(tags_path.read_text(encoding="utf-8"))

    # 6. ri_sp_coverage.json (L3)
    risp_path = d / "ri_sp_coverage.json"
    if risp_path.exists():
        result["ri_sp_coverage"] = json.loads(risp_path.read_text(encoding="utf-8"))

    # 7. cur_report.csv (L3)
    cur_path = d / "cur_report.csv"
    if cur_path.exists():
        result["cur_report"] = summarize_cur(cur_path.read_text(encoding="utf-8"))

    # 8. cloudwatch_format.json (L3)
    cw_path = d / "metrics" / "cloudwatch_format.json"
    if cw_path.exists():
        result["cloudwatch_format"] = json.loads(cw_path.read_text(encoding="utf-8"))

    # Detect level based on available files
    if "business_metrics" in result or "tags_inventory" in result:
        result["level"] = "L3" if "ri_sp_coverage" in result or "cur_report" in result else "L2"
    else:
        result["level"] = "L1"

    return result


def summarize_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize metrics for LLM — full datapoints are too large to send.

    For each resource+metric, compute: mean, max, min, zero_pct, trend.
    """
    summary: Dict[str, Any] = {
        "metadata": raw.get("metadata", {}),
        "resources": {},
    }

    for res_name, res_data in raw.get("resources", {}).items():
        res_summary: Dict[str, Any] = {
            "resource_type": res_data.get("resource_type", ""),
            "metrics": {},
        }

        for metric_name, metric_data in res_data.get("metrics", {}).items():
            points = metric_data.get("datapoints", [])
            if not points:
                continue

            n = len(points)
            mean_val = sum(points) / n
            max_val = max(points)
            min_val = min(points)
            zero_count = sum(1 for p in points if p == 0)
            zero_pct = round(zero_count / n * 100, 1)

            # Simple trend: compare first half avg vs second half avg
            mid = n // 2
            first_half = sum(points[:mid]) / max(mid, 1)
            second_half = sum(points[mid:]) / max(n - mid, 1)
            if first_half > 0:
                trend_pct = round((second_half - first_half) / first_half * 100, 1)
            else:
                trend_pct = 0

            res_summary["metrics"][metric_name] = {
                "unit": metric_data.get("unit", ""),
                "mean": round(mean_val, 2),
                "max": round(max_val, 2),
                "min": round(min_val, 2),
                "zero_pct": zero_pct,
                "trend_pct": trend_pct,
                "points_count": n,
            }

        summary["resources"][res_name] = res_summary

    return summary


def summarize_cur(csv_text: str) -> Dict[str, Any]:
    """Summarize CUR CSV — too large to send raw."""
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    # Group by product code
    by_product: Dict[str, float] = {}
    total_cost = 0
    for row in rows:
        product = row.get("lineItem/ProductCode", "Unknown")
        cost = float(row.get("lineItem/UnblendedCost", 0))
        by_product[product] = by_product.get(product, 0) + cost
        total_cost += cost

    return {
        "total_rows": len(rows),
        "total_cost": round(total_cost, 2),
        "by_product": {k: round(v, 2) for k, v in sorted(by_product.items(), key=lambda x: -x[1])},
        "date_range": {
            "start": rows[0].get("lineItem/UsageStartDate", "")[:10] if rows else "",
            "end": rows[-1].get("lineItem/UsageStartDate", "")[:10] if rows else "",
        },
    }


def build_context_text(data: Dict[str, Any]) -> str:
    """Build a text context string from parsed problem data for LLM consumption."""
    parts: list[str] = []

    # Terraform
    if "terraform" in data:
        parts.append("=== TERRAFORM (main.tf) ===")
        parts.append(data["terraform"])

    # Metrics summary
    if "metrics" in data:
        parts.append("\n=== METRICS SUMMARY (30-day) ===")
        for res_name, res in data["metrics"].get("resources", {}).items():
            parts.append(f"\nResource: {res_name} ({res['resource_type']})")
            for m_name, m_data in res.get("metrics", {}).items():
                parts.append(
                    f"  {m_name}: mean={m_data['mean']} max={m_data['max']} "
                    f"min={m_data['min']} zero={m_data['zero_pct']}% "
                    f"trend={m_data['trend_pct']}%"
                )

    # Cost report
    if "cost_report" in data:
        cr = data["cost_report"]
        parts.append("\n=== COST REPORT (6 months) ===")
        summary = cr.get("summary", {})
        parts.append(f"Avg monthly total: ${summary.get('avg_monthly_total', 0)}")
        parts.append(f"Avg monthly waste: ${summary.get('avg_monthly_waste', 0)}")
        parts.append(f"Waste services: {summary.get('waste_services', [])}")
        for m in cr.get("monthly_data", []):
            parts.append(f"  {m['label']}: total=${m['total_spend_usd']} waste=${m['waste_usd']} ({m['waste_pct']}%)")

    # Business metrics (L2+)
    if "business_metrics" in data:
        bm = data["business_metrics"]
        ue = bm.get("current_unit_economics", {})
        parts.append("\n=== BUSINESS METRICS ===")
        parts.append(f"Cost per order: ${ue.get('cost_per_order', 'N/A')}")
        parts.append(f"Cost per 1K requests: ${ue.get('cost_per_1k_requests', 'N/A')}")
        parts.append(f"Cost/revenue ratio: {ue.get('cost_to_revenue_pct', 'N/A')}%")

    # Tags inventory (L2+)
    if "tags_inventory" in data:
        ti = data["tags_inventory"]
        s = ti.get("summary", {})
        parts.append("\n=== TAGS INVENTORY ===")
        parts.append(f"Coverage: {s.get('tag_coverage_pct', 0)}%")
        parts.append(f"Non-compliant resources: {s.get('non_compliant', 0)}/{s.get('total_resources', 0)}")
        for r in ti.get("resources", []):
            if r.get("missing_tags"):
                parts.append(f"  {r['resource_name']}: missing {r['missing_tags']}")

    # RI/SP coverage (L3)
    if "ri_sp_coverage" in data:
        risp = data["ri_sp_coverage"]
        cov = risp.get("coverage_summary", {})
        parts.append("\n=== RI/SP COVERAGE ===")
        parts.append(f"RI: {cov.get('ri_coverage_pct', 0)}% | SP: {cov.get('sp_coverage_pct', 0)}% | On-Demand: {cov.get('on_demand_pct', 0)}%")
        pot = risp.get("potential_savings", {})
        if pot.get("with_1yr_sp"):
            parts.append(f"Potential savings (1yr SP): ${pot['with_1yr_sp'].get('monthly_savings_usd', 0)}/mo")

    # CUR summary (L3)
    if "cur_report" in data:
        cur = data["cur_report"]
        parts.append("\n=== CUR REPORT SUMMARY ===")
        parts.append(f"Total cost: ${cur.get('total_cost', 0)} ({cur.get('total_rows', 0)} line items)")
        for product, cost in cur.get("by_product", {}).items():
            parts.append(f"  {product}: ${cost}")

    return "\n".join(parts)
