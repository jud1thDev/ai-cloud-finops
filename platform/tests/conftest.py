"""Shared test fixtures."""

from pathlib import Path

import pytest

from finops_sim.config import SCENARIOS_DIR


@pytest.fixture
def scenarios_dir() -> Path:
    return SCENARIOS_DIR
