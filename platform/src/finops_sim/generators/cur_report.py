"""Generate AWS CUR (Cost and Usage Report) CSV for L3 scenarios."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import COST_HISTORY_MONTHS
from finops_sim.generators.base import GenerationContext
from finops_sim.utils.random_helpers import SeededRandom

# Standard CUR columns
CUR_COLUMNS = [
    "identity/LineItemId",
    "identity/TimeInterval",
    "lineItem/UsageStartDate",
    "lineItem/UsageEndDate",
    "lineItem/ProductCode",
    "lineItem/UsageType",
    "lineItem/Operation",
    "lineItem/UsageAmount",
    "lineItem/UnblendedCost",
    "lineItem/BlendedCost",
    "lineItem/LineItemType",
    "product/region",
    "resourceTags/user:Service",
    "resourceTags/user:Team",
    "resourceTags/user:Env",
]

# Map resource types to AWS product codes and usage types
_PRODUCT_MAP = {
    "aws_instance": ("AmazonEC2", "BoxUsage:{instance_type}"),
    "aws_ebs_volume": ("AmazonEC2", "EBS:VolumeUsage.{volume_type}"),
    "aws_db_instance": ("AmazonRDS", "InstanceUsage:{instance_class}"),
    "aws_s3_bucket": ("AmazonS3", "TimedStorage-ByteHrs"),
    "aws_lambda_function": ("AWSLambda", "Lambda-GB-Second"),
    "aws_nat_gateway": ("AmazonEC2", "NatGateway-Hours"),
    "aws_dynamodb_table": ("AmazonDynamoDB", "PayPerRequestThroughput"),
    "aws_eks_cluster": ("AmazonEKS", "AmazonEKS-Hours:perCluster"),
    "aws_eks_node_group": ("AmazonEC2", "BoxUsage:{instance_types}"),
    "aws_ecs_service": ("AmazonECS", "Fargate-vCPU-Hours:perCPU"),
    "aws_redshift_cluster": ("AmazonRedshift", "Node:{node_type}"),
    "aws_lb": ("ElasticLoadBalancing", "LoadBalancerUsage"),
}


class CURReportGenerator:
    """Generates AWS CUR-format CSV with daily line items.

    Expands the CostReportGenerator's monthly data into daily granularity
    matching AWS Cost and Usage Report standard columns.
    """

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed + 6000)

    def generate(self) -> str:
        """Generate CUR CSV content as a string."""
        scenario = self.ctx.scenario
        manifest = self.ctx.manifest
        cost = scenario.cost_profile
        monthly_waste = cost.monthly_waste_usd

        # Total monthly spend
        base_spend = monthly_waste * self.rng.floating(5.0, 15.0)

        rows: List[Dict[str, str]] = []
        end_date = datetime(2026, 3, 18)

        # Generate daily line items for last 30 days
        for day_offset in range(30):
            day = end_date - timedelta(days=29 - day_offset)
            day_str = day.strftime("%Y-%m-%dT00:00:00Z")
            day_end_str = (day + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            interval = f"{day_str}/{day_end_str}"

            if manifest:
                for inst in manifest.instances:
                    product_code, usage_type_tmpl = _PRODUCT_MAP.get(
                        inst.resource_type, ("AmazonEC2", "Other")
                    )
                    usage_type = usage_type_tmpl.format(**inst.config)

                    # Daily cost: problem resources carry the waste
                    if inst.is_problem:
                        daily_cost = monthly_waste / 30 / max(
                            len(manifest.problem_resources), 1
                        )
                    else:
                        daily_cost = (base_spend - monthly_waste) / 30 / max(
                            len(manifest.decoy_resources), 1
                        )

                    daily_cost *= self.rng.floating(0.85, 1.15)

                    # Extract tags from config or use defaults
                    svc_tag = inst.config.get("service_tag", "")
                    team_tag = inst.config.get("team_tag", "")
                    env_tag = inst.config.get("env_tag", "prod")

                    rows.append({
                        "identity/LineItemId": str(uuid.UUID(int=self.rng.integer(0, 2**128 - 1))),
                        "identity/TimeInterval": interval,
                        "lineItem/UsageStartDate": day_str,
                        "lineItem/UsageEndDate": day_end_str,
                        "lineItem/ProductCode": product_code,
                        "lineItem/UsageType": usage_type,
                        "lineItem/Operation": "RunInstances",
                        "lineItem/UsageAmount": str(round(self.rng.floating(1.0, 24.0), 4)),
                        "lineItem/UnblendedCost": str(round(daily_cost, 6)),
                        "lineItem/BlendedCost": str(round(daily_cost * self.rng.floating(0.95, 1.05), 6)),
                        "lineItem/LineItemType": "Usage",
                        "product/region": "us-east-1",
                        "resourceTags/user:Service": svc_tag,
                        "resourceTags/user:Team": team_tag,
                        "resourceTags/user:Env": env_tag,
                    })

        # Write CSV string
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CUR_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def write(self, output_dir: Path) -> Path:
        csv_content = self.generate()
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "cur_report.csv"
        out_path.write_text(csv_content, encoding="utf-8")
        return out_path
