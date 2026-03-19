"""Student CLI for FinOps AI study platform.

Usage:
    finops-study pull --week 1
    finops-study validate ./my_output/analysis.json
    finops-study submit ./my_output/ --week 1 --scenario L1-002
    finops-study status --week 1
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0")
def main():
    """FinOps AI Study Platform — Student CLI"""
    pass


@main.command()
@click.option("--week", required=True, type=int, help="Week number")
@click.option("--output", default=".", help="Local directory to save problems")
def pull(week: int, output: str):
    """Download your assigned problems for the week."""
    from finops_study.github_client import GitHubClient

    username = os.environ.get("GITHUB_USERNAME", "")
    if not username:
        click.echo("Error: Set GITHUB_USERNAME environment variable", err=True)
        sys.exit(1)

    client = GitHubClient()
    remote_path = f"problems/week-{week:02d}/{username}"
    local_dir = Path(output) / f"week-{week:02d}"

    click.echo(f"Pulling problems for {username}, week {week}...")
    try:
        files = client.download_directory(remote_path, local_dir)
        click.echo(f"Downloaded {len(files)} files to {local_dir}/")
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--level", default="L1", type=click.Choice(["L1", "L2", "L3"]), help="Scenario level")
def validate(path: str, level: str):
    """Validate an AI output JSON file against the spec."""
    from finops_study.validator import validate_file

    file_path = Path(path)
    errors = validate_file(file_path, level)

    if not errors:
        click.echo(click.style("VALID", fg="green", bold=True) + f" — {file_path.name} passes {level} schema")
    else:
        click.echo(click.style("INVALID", fg="red", bold=True) + f" — {len(errors)} error(s):")
        for e in errors:
            click.echo(f"  - {e}")
        sys.exit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--week", required=True, type=int, help="Week number")
@click.option("--scenario", required=True, help="Scenario ID (e.g., L1-002)")
@click.option("--notify-slack", is_flag=True, help="Send alerts to Slack after submission")
def submit(path: str, week: int, scenario: str, notify_slack: bool):
    """Submit your analysis for grading."""
    from finops_study.github_client import GitHubClient
    from finops_study.validator import validate_file

    username = os.environ.get("GITHUB_USERNAME", "")
    if not username:
        click.echo("Error: Set GITHUB_USERNAME environment variable", err=True)
        sys.exit(1)

    file_path = Path(path)
    if file_path.is_dir():
        # Look for analysis.json in directory
        file_path = file_path / "analysis.json"
        if not file_path.exists():
            click.echo(f"Error: No analysis.json found in {path}", err=True)
            sys.exit(1)

    # Validate first
    level = scenario.split("-")[0] if "-" in scenario else "L1"
    errors = validate_file(file_path, level)
    if errors:
        click.echo(click.style("Validation failed", fg="red") + f" — fix errors before submitting:")
        for e in errors[:5]:
            click.echo(f"  - {e}")
        sys.exit(1)

    # Submit
    content = file_path.read_text(encoding="utf-8")
    client = GitHubClient()
    remote_path = f"submissions/week-{week:02d}/{username}/{scenario}.json"

    click.echo(f"Submitting {file_path.name} → {remote_path}...")
    try:
        client.create_or_update_file(
            remote_path,
            content,
            f"Submit {scenario} analysis for week {week} by {username}",
        )
        click.echo(click.style("Submitted!", fg="green", bold=True))
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Optional Slack notification
    if notify_slack:
        try:
            data = json.loads(content)
            from finops_study.slack import send_alerts
            send_alerts(data.get("alerts", []), scenario, username)
        except Exception as e:
            click.echo(f"Slack notification failed: {e}", err=True)


@main.command()
@click.option("--week", required=True, type=int, help="Week number")
def status(week: int):
    """Check submission and scoring status for the week."""
    from finops_study.github_client import GitHubClient

    username = os.environ.get("GITHUB_USERNAME", "")
    if not username:
        click.echo("Error: Set GITHUB_USERNAME environment variable", err=True)
        sys.exit(1)

    client = GitHubClient()
    week_str = f"week-{week:02d}"

    # Check submissions
    click.echo(f"\n=== Week {week} Status for {username} ===\n")

    try:
        submissions = client.list_contents(f"submissions/{week_str}/{username}")
        click.echo(f"Submissions: {len(submissions)} file(s)")
        for s in submissions:
            click.echo(f"  - {s['name']}")
    except RuntimeError:
        click.echo("Submissions: none")

    # Check scores
    try:
        score_content = client.get_file(f"scores/{week_str}/{username}.json")
        scores = json.loads(score_content)
        click.echo(f"\nScore: {scores.get('total', 0)}/{scores.get('max_total', 0)} ({scores.get('percentage', 0)}%)")
        for sid, result in scores.get("scenarios", {}).items():
            click.echo(f"  {sid}: {result.get('total', 0)}/{result.get('max_total', 0)}")
    except RuntimeError:
        click.echo("\nScores: not yet available")

    click.echo()


if __name__ == "__main__":
    main()
