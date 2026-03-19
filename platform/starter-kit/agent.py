#!/usr/bin/env python3
"""FinOps AI Agent — Starter Template

Usage:
    python agent.py ./path/to/problem/L1-001/
    python agent.py ./path/to/problem/L1-001/ --validate-only
    python agent.py ./path/to/problem/L1-001/ --output ./my_analysis.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config import (
    MODEL_PROVIDER, OLLAMA_URL, OLLAMA_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    MAX_TOKENS, TEMPERATURE,
)
from file_reader import read_problem, build_context_text
from output_builder import extract_json_from_response, validate_output, save_output


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM based on config. Returns raw response text."""

    if MODEL_PROVIDER == "ollama":
        return _call_ollama(system_prompt, user_prompt)
    elif MODEL_PROVIDER == "openai":
        return _call_openai(system_prompt, user_prompt)
    elif MODEL_PROVIDER == "claude":
        return _call_claude(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown provider: {MODEL_PROVIDER}")


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Call local Ollama model."""
    import urllib.request

    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": MAX_TOKENS,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"]


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API."""
    import urllib.request

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Call Anthropic Claude API."""
    import urllib.request

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]


def load_prompt(name: str) -> str:
    """Load prompt from prompts/ directory."""
    path = Path(__file__).parent / "prompts" / name
    return path.read_text(encoding="utf-8")


def run_analysis(problem_dir: str, output_path: str = "analysis.json") -> dict:
    """Main analysis pipeline."""
    print(f"Reading problem from: {problem_dir}")
    data = read_problem(problem_dir)
    level = data["level"]
    print(f"Detected level: {level}")

    # Build context text from all available files
    context = build_context_text(data)

    # Load prompts
    system_prompt = load_prompt("system.md")
    level_prompt = load_prompt(f"{level}_analyze.md")

    # Combine into user prompt
    user_prompt = f"{level_prompt}\n\n---\n\n{context}"

    # Call LLM
    print(f"Calling {MODEL_PROVIDER} ({OLLAMA_MODEL if MODEL_PROVIDER == 'ollama' else ''})...")
    response = call_llm(system_prompt, user_prompt)

    # Parse response
    print("Parsing response...")
    try:
        output = extract_json_from_response(response)
    except ValueError:
        print("ERROR: Could not extract JSON from LLM response.")
        print("Raw response:")
        print(response[:2000])
        sys.exit(1)

    # Validate
    errors = validate_output(output, level)
    if errors:
        print(f"WARNING: Output has {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("Output validation: PASS")

    # Save
    save_output(output, output_path)
    print(f"Saved to: {output_path}")

    # Print summary
    summary = output.get("summary", {})
    problems = output.get("analysis", {}).get("problems_found", [])
    print(f"\n=== Analysis Result ===")
    print(f"Issues found: {summary.get('total_issues_found', len(problems))}")
    print(f"Estimated savings: ${summary.get('total_monthly_savings_usd', 0)}/month")
    print(f"Confidence: {summary.get('confidence_score', 0)}%")
    for p in problems:
        print(f"  [{p.get('severity', '?')}] {p.get('resource', '?')}: {p.get('recommendation', '')[:60]}")

    return output


def main():
    parser = argparse.ArgumentParser(description="FinOps AI Agent")
    parser.add_argument("problem_dir", help="Path to problem directory (e.g., ./L1-001/)")
    parser.add_argument("--output", "-o", default="analysis.json", help="Output file path")
    parser.add_argument("--validate-only", action="store_true", help="Only validate an existing output file")
    args = parser.parse_args()

    if args.validate_only:
        # Just validate an existing file
        try:
            output = json.loads(Path(args.output).read_text(encoding="utf-8"))
            data = read_problem(args.problem_dir)
            errors = validate_output(output, data["level"])
            if errors:
                print(f"INVALID — {len(errors)} error(s):")
                for e in errors:
                    print(f"  - {e}")
                sys.exit(1)
            else:
                print("VALID")
        except FileNotFoundError:
            print(f"File not found: {args.output}")
            sys.exit(1)
    else:
        run_analysis(args.problem_dir, args.output)


if __name__ == "__main__":
    main()
