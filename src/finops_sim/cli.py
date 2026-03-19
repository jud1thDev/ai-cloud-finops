"""CLI interface for finops-sim (Phase 4 full implementation)."""

from __future__ import annotations

import click


@click.group()
@click.version_option()
def main() -> None:
    """FinOps simulation problem generator."""


@main.group()
def catalog() -> None:
    """Browse the scenario catalog."""


@catalog.command("list")
@click.option("--level", type=click.Choice(["L1", "L2", "L3"]), default=None)
def catalog_list(level: str | None) -> None:
    """List available scenarios."""
    from finops_sim.catalog.loader import list_scenarios

    scenarios = list_scenarios(level=level)
    for s in scenarios:
        click.echo(f"{s.id}  [{s.level.value}]  {s.title}")


@catalog.command("show")
@click.argument("scenario_id")
def catalog_show(scenario_id: str) -> None:
    """Show details of a scenario."""
    from finops_sim.catalog.loader import get_scenario

    s = get_scenario(scenario_id)
    click.echo(f"ID:       {s.id}")
    click.echo(f"Title:    {s.title}")
    click.echo(f"Level:    {s.level.value}")
    click.echo(f"Category: {s.category}")
    click.echo(f"Services: {', '.join(s.aws_services)}")
    click.echo(f"\n{s.description}")
    click.echo(f"Detection: {s.detection_method}")
    click.echo(f"Waste:     ${s.cost_profile.monthly_waste_usd}/mo")
    click.echo(f"Severity:  {s.answer.severity}")


@main.group()
def generate() -> None:
    """Generate simulation problems."""


@generate.command("fixed")
@click.option("--scenario-id", required=True, help="Scenario ID (e.g. L1-001)")
@click.option("--output", "-o", default="./output", help="Output directory")
@click.option("--seed", default=42, type=int, help="Random seed")
@click.option("--use-llm", is_flag=True, default=False, help="Use Claude API for richer content")
def generate_fixed(scenario_id: str, output: str, seed: int, use_llm: bool) -> None:
    """Generate a fixed scenario."""
    from finops_sim.generators.orchestrator import generate_fixed as _gen

    llm_label = " [LLM]" if use_llm else ""
    click.echo(f"Generating scenario {scenario_id} (seed={seed}){llm_label}...")
    result = _gen(scenario_id=scenario_id, output_dir=output, seed=seed, use_llm=use_llm)
    click.echo(f"Output: {result['output_dir']}")
    click.echo(f"Resources: {result['resource_count']} ({result['problem_count']} problem, {result['decoy_count']} decoy)")
    for label, path in result["files"].items():
        click.echo(f"  {label}: {path}")


@generate.command("auto")
@click.option("--level", type=click.Choice(["L1", "L2", "L3"]), default="L1")
@click.option("--num-problems", default=3, type=int)
@click.option("--seed", default=42, type=int)
@click.option("--output", "-o", default="./output")
@click.option("--use-llm", is_flag=True, default=False, help="Use Claude API for richer content")
def generate_auto(level: str, num_problems: int, seed: int, output: str, use_llm: bool) -> None:
    """Auto-generate scenario combinations."""
    from finops_sim.generators.orchestrator import generate_auto as _gen

    llm_label = " [LLM]" if use_llm else ""
    click.echo(f"Auto-generating {num_problems} {level} problems (seed={seed}){llm_label}...")
    results = _gen(level=level, num_problems=num_problems, output_dir=output, seed=seed, use_llm=use_llm)
    click.echo(f"Company: {results[0]['company']}")
    click.echo(f"Generated {len(results)} scenarios:")
    for r in results:
        click.echo(f"  {r['scenario_id']}: {r['resource_count']} resources → {r['output_dir']}")


@main.command()
@click.argument("output_dir", type=click.Path(exists=True))
def validate(output_dir: str) -> None:
    """Validate generated output artifacts."""
    from pathlib import Path

    from finops_sim.utils.validators import validate_output_dir

    p = Path(output_dir)

    # Check if it's a single scenario dir or a parent with multiple
    if (p / "main.tf").exists():
        dirs = [p]
    else:
        dirs = sorted(d for d in p.iterdir() if d.is_dir() and (d / "main.tf").exists())

    if not dirs:
        click.echo("No scenario output directories found.", err=True)
        raise SystemExit(1)

    total_errors = 0
    for d in dirs:
        errors = validate_output_dir(d)
        name = d.name
        if errors:
            click.echo(f"FAIL {name}:")
            for e in errors:
                click.echo(f"  - {e}")
            total_errors += len(errors)
        else:
            click.echo(f"OK   {name}")

    if total_errors:
        click.echo(f"\n{total_errors} error(s) found.")
        raise SystemExit(1)
    else:
        click.echo(f"\nAll {len(dirs)} scenario(s) valid.")


if __name__ == "__main__":
    main()
