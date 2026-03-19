"""Scenario auto-selection for auto-generate mode."""

from __future__ import annotations

from typing import List, Optional

from finops_sim.catalog.loader import list_scenarios
from finops_sim.generators.base import ScenarioDefinition
from finops_sim.utils.random_helpers import SeededRandom


def select_scenarios(
    level: str,
    num_problems: int,
    seed: int,
    category: Optional[str] = None,
) -> List[ScenarioDefinition]:
    """Select a random subset of scenarios for auto-generation.

    Picks *num_problems* distinct scenarios from the given level,
    optionally filtered by category. Uses a seeded RNG for
    reproducibility.
    """
    rng = SeededRandom(seed)
    candidates = list_scenarios(level=level)

    if category:
        candidates = [s for s in candidates if s.category == category]

    if not candidates:
        raise ValueError(
            "No scenarios found for level=%r, category=%r" % (level, category)
        )

    num = min(num_problems, len(candidates))
    selected = rng.sample(candidates, num)
    return sorted(selected, key=lambda s: s.id)
