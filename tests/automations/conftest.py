"""Shared fixtures for automation unit tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.automations.simulation import AutomationSimulator

AUTOMATIONS_DIR = Path(__file__).parent.parent.parent / "automations"


@pytest.fixture
def pv_sim() -> AutomationSimulator:
    """
    AutomationSimulator pre-loaded with pv_smart_outlets.yaml.

    Initial state: sensor at 0 W, outlet off.
    Each test starts from a known-clean slate.
    """
    sim = AutomationSimulator(AUTOMATIONS_DIR / "pv_smart_outlets.yaml")
    sim.set_state("sensor.pv_grid_return_power", "0")
    sim.set_state("switch.smart_outlet_1", "off")
    return sim
