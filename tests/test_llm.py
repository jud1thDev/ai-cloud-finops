"""Tests for LLM module (passthrough and interface)."""

from __future__ import annotations

from pathlib import Path

import pytest

from finops_sim.llm.interface import LLMInterface
from finops_sim.llm.passthrough import PassthroughLLM


SAMPLE_PROFILE = {
    "company_name": "TestCorp",
    "industry": "SaaS",
    "employee_count": 100,
    "growth_stage": "성장기",
    "monthly_cloud_spend_usd": 25000,
    "typical_services": ["EC2", "RDS", "S3"],
}


class TestPassthroughLLM:
    def test_implements_interface(self) -> None:
        llm = PassthroughLLM()
        assert isinstance(llm, LLMInterface)

    def test_generate_company_story(self) -> None:
        llm = PassthroughLLM()
        story = llm.generate_company_story(
            SAMPLE_PROFILE,
            scenario_title="중지된 EC2",
            scenario_description="stopped EC2",
        )
        assert "TestCorp" in story
        assert "SaaS" in story
        assert len(story) > 50

    def test_enrich_readme(self) -> None:
        llm = PassthroughLLM()
        base = "# Title\n\n## 배경\n\n기본 배경.\n\n## 과제\n\n과제 내용"
        enriched = llm.enrich_readme(base, SAMPLE_PROFILE)
        assert "## 배경" in enriched
        assert "TestCorp" in enriched

    def test_generate_hint(self) -> None:
        llm = PassthroughLLM()
        hint = llm.generate_hint("중지된 EC2", "unused", "L1")
        assert len(hint) > 10

    def test_hint_varies_by_category(self) -> None:
        llm = PassthroughLLM()
        h1 = llm.generate_hint("test", "unused", "L1")
        h2 = llm.generate_hint("test", "overprovisioning", "L2")
        assert h1 != h2


class TestClaudeLLMImportGuard:
    def test_import_error_without_anthropic(self) -> None:
        """ClaudeLLM should raise ImportError if anthropic not installed."""
        from finops_sim.llm.claude import ClaudeLLM

        llm = ClaudeLLM()
        # Accessing client should fail since anthropic isn't installed
        with pytest.raises((ImportError, ValueError)):
            _ = llm.client


class TestOrchestratorWithPassthrough:
    def test_fixed_with_hint_file(self, tmp_path: Path) -> None:
        from finops_sim.generators.orchestrator import generate_fixed

        result = generate_fixed("L1-001", str(tmp_path), seed=42, use_llm=False)
        hint_path = Path(result["files"]["hint"])
        assert hint_path.exists()
        hint_text = hint_path.read_text()
        assert len(hint_text) > 10
        assert result["llm_used"] is False
