"""Terraform HCL generator."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

from finops_sim.config import HCL_TEMPLATES_DIR
from finops_sim.generators.base import (
    GenerationContext,
    ResourceInstance,
    ResourceManifest,
    ResourceSpec,
)
from finops_sim.utils.random_helpers import SeededRandom

TEMPLATE_MAP: Dict[str, str] = {
    "aws_instance": "compute.hcl.j2",
    "aws_lambda_function": "compute.hcl.j2",
    "aws_autoscaling_group": "compute.hcl.j2",
    "aws_ecs_service": "container.hcl.j2",
    "aws_eks_cluster": "compute.hcl.j2",
    "aws_eks_node_group": "container.hcl.j2",
    "aws_ebs_volume": "storage.hcl.j2",
    "aws_ebs_snapshot": "storage.hcl.j2",
    "aws_s3_bucket": "storage.hcl.j2",
    "aws_s3_bucket_replication_configuration": "storage.hcl.j2",
    "aws_ecr_repository": "storage.hcl.j2",
    "aws_db_instance": "database.hcl.j2",
    "aws_db_proxy": "database.hcl.j2",
    "aws_elasticache_replication_group": "database.hcl.j2",
    "aws_dynamodb_table": "database.hcl.j2",
    "aws_redshift_cluster": "database.hcl.j2",
    "aws_nat_gateway": "network.hcl.j2",
    "aws_vpc_endpoint": "network.hcl.j2",
    "aws_ec2_transit_gateway": "network.hcl.j2",
    "aws_lb": "network.hcl.j2",
    "aws_eip": "network.hcl.j2",
    "aws_vpn_connection": "network.hcl.j2",
    "aws_dx_connection": "network.hcl.j2",
    "aws_cloudfront_distribution": "network.hcl.j2",
    "aws_subnet": "network.hcl.j2",
    "aws_vpc_peering_connection": "network.hcl.j2",
    "aws_ami": "compute.hcl.j2",
    "aws_cloudwatch_log_group": "compute.hcl.j2",
    "aws_cloudwatch_metric_alarm": "compute.hcl.j2",
    "aws_sqs_queue": "network.hcl.j2",
    "aws_kinesis_stream": "network.hcl.j2",
    "aws_kinesis_stream_consumer": "network.hcl.j2",
    "aws_glue_catalog_table": "database.hcl.j2",
    "aws_ec2_reserved_instances": "database.hcl.j2",
    "aws_route_table": "network.hcl.j2",
    "aws_ec2_transit_gateway_vpc_attachment": "network.hcl.j2",
    "aws_organization": "network.hcl.j2",
    "aws_account": "network.hcl.j2",
}

_PROVIDER_HEADER = """\
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
"""


class TerraformGenerator:
    """Generates Terraform HCL files from a scenario definition."""

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed)
        self.env = Environment(
            loader=FileSystemLoader(str(HCL_TEMPLATES_DIR)),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ------------------------------------------------------------------
    # Manifest building
    # ------------------------------------------------------------------

    def _expand_specs(
        self,
        specs: List[ResourceSpec],
        is_problem: bool,
    ) -> List[ResourceInstance]:
        """Expand a list of ResourceSpecs into concrete ResourceInstances."""
        instances: List[ResourceInstance] = []
        for spec in specs:
            # Derive a short prefix from the resource type
            # e.g. "aws_instance" -> "instance", "aws_s3_bucket" -> "s3-bucket"
            raw = spec.type[4:] if spec.type.startswith("aws_") else spec.type
            prefix = raw.replace("_", "-")
            for idx in range(spec.count):
                name = self.rng.resource_name(prefix=prefix)
                instances.append(
                    ResourceInstance(
                        resource_type=spec.type,
                        resource_name=name,
                        config=dict(spec.config),
                        is_problem=is_problem,
                        group_index=idx,
                    )
                )
        return instances

    def build_manifest(self) -> ResourceManifest:
        """Build a ResourceManifest from the scenario definition."""
        manifest = ResourceManifest()
        manifest.instances.extend(
            self._expand_specs(self.ctx.scenario.problem_resources, is_problem=True)
        )
        manifest.instances.extend(
            self._expand_specs(self.ctx.scenario.decoy_resources, is_problem=False)
        )
        self.ctx.manifest = manifest
        return manifest

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_resource(self, inst: ResourceInstance) -> str:
        """Render a single ResourceInstance to HCL using its Jinja2 macro."""
        template_file = TEMPLATE_MAP.get(inst.resource_type)
        if template_file is None:
            raise ValueError(
                f"No HCL template mapping for resource type: {inst.resource_type}"
            )

        template = self.env.get_template(template_file)
        # Templates define macros named after the resource type (e.g. aws_instance).
        # Access via template.module to call the macro directly.
        module = template.module
        macro_name = inst.resource_type
        macro_fn = getattr(module, macro_name, None)

        r = {
            "resource_type": inst.resource_type,
            "resource_name": inst.resource_name,
            "config": inst.config,
            "is_problem": inst.is_problem,
            "group_index": inst.group_index,
        }

        if macro_fn is not None:
            return macro_fn(r)

        # Fallback: generate a generic resource block
        return self._render_generic(r)

    @staticmethod
    def _render_generic(r: Dict[str, Any]) -> str:
        """Render a generic HCL block for resource types without a macro."""
        lines = [
            'resource "%s" "%s" {' % (r["resource_type"], r["resource_name"]),
        ]
        for key, val in r["config"].items():
            if isinstance(val, (list, dict)):
                continue  # skip complex nested values
            if isinstance(val, bool):
                lines.append("  %s = %s" % (key, str(val).lower()))
            elif isinstance(val, (int, float)):
                lines.append("  %s = %s" % (key, val))
            else:
                lines.append('  %s = "%s"' % (key, val))
        lines.append("")
        lines.append("  tags = {")
        lines.append('    Name = "%s"' % r["resource_name"])
        lines.append("  }")
        lines.append("}")
        return "\n".join(lines)

    def render(self) -> str:
        """Render all resources in the manifest to a complete HCL string."""
        if self.ctx.manifest is None:
            self.build_manifest()

        assert self.ctx.manifest is not None
        blocks: List[str] = [_PROVIDER_HEADER]
        for inst in self.ctx.manifest.instances:
            block = self._render_resource(inst)
            if block.strip():
                blocks.append(block)

        return "\n".join(blocks) + "\n"

    # ------------------------------------------------------------------
    # File writing
    # ------------------------------------------------------------------

    def write(self, output_dir: Path) -> Path:
        """Write rendered HCL to *output_dir*/main.tf and return the path."""
        output_dir.mkdir(parents=True, exist_ok=True)
        hcl = self.render()
        target = output_dir / "main.tf"
        target.write_text(hcl, encoding="utf-8")
        return target
