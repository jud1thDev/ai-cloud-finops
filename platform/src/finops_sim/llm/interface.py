"""LLM interface protocol for pluggable backends."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class LLMInterface(Protocol):
    """Protocol that any LLM backend must implement."""

    def generate_company_story(
        self,
        company_profile: Dict[str, Any],
        scenario_title: str,
        scenario_description: str,
    ) -> str:
        """Generate a realistic company background narrative."""
        ...

    def enrich_readme(
        self,
        base_readme: str,
        company_profile: Dict[str, Any],
    ) -> str:
        """Enhance a template README with natural language context."""
        ...

    def generate_hint(
        self,
        scenario_title: str,
        scenario_category: str,
        level: str,
    ) -> str:
        """Generate a subtle hint for the solver without giving away the answer."""
        ...
