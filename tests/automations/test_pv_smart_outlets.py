"""
Unit tests for automations/pv_smart_outlets.yaml.

All tests use the `pv_sim` fixture (AutomationSimulator pre-loaded with the
YAML, outlet starts OFF, sensor starts at 0 W).

Thresholds under test:
  Turn ON  when surplus crosses above 25 W   (outlet_watts + hysteresis_watts = 20 + 5)
  Turn OFF when surplus crosses below 15 W   (outlet_watts - hysteresis_watts = 20 - 5)

Dead zone (no action): [15 W, 25 W]
"""
from tests.automations.simulation import AutomationSimulator, ServiceCall


# ── ON trigger: upward crossings ──────────────────────────────────────────────

def test_turn_on_when_surplus_crosses_above_threshold(pv_sim: AutomationSimulator):
    """0 W → 30 W: surplus crosses above 25 W, outlet is off → turn_on fires."""
    pv_sim.update_state("sensor.pv_grid_return_power", "30")
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_on", ["switch.smart_outlet_1"])
    ]


def test_turn_on_at_one_watt_above_threshold(pv_sim: AutomationSimulator):
    """0 W → 26 W: barely crosses above 25 W → turn_on fires."""
    pv_sim.update_state("sensor.pv_grid_return_power", "26")
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_on", ["switch.smart_outlet_1"])
    ]


def test_no_turn_on_at_exactly_threshold(pv_sim: AutomationSimulator):
    """0 W → 20 W: value equals threshold exactly, does NOT cross above → no trigger."""
    pv_sim.update_state("sensor.pv_grid_return_power", "20")
    assert pv_sim.service_calls == []


def test_no_turn_on_below_threshold(pv_sim: AutomationSimulator):
    """0 W → 15 W: surplus stays below threshold → no trigger."""
    pv_sim.update_state("sensor.pv_grid_return_power", "15")
    assert pv_sim.service_calls == []


def test_no_turn_on_when_outlet_already_on(pv_sim: AutomationSimulator):
    """
    State guard: outlet already on → condition blocks turn_on from firing again.

    This prevents repeated service calls when the sensor oscillates above threshold.
    """
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.update_state("sensor.pv_grid_return_power", "30")
    assert pv_sim.service_calls == []


# ── ON buffer zone (new requirement) ─────────────────────────────────────────

def test_no_turn_on_when_surplus_in_on_buffer_zone(pv_sim: AutomationSimulator):
    """0 W → 21 W: above outlet draw (20 W) but inside the 5 W ON buffer → must NOT fire."""
    pv_sim.update_state("sensor.pv_grid_return_power", "21")
    assert pv_sim.service_calls == []


def test_no_turn_on_at_new_on_threshold_exactly(pv_sim: AutomationSimulator):
    """0 W → 25 W: exactly at the new ON threshold — does NOT cross above it → no trigger."""
    pv_sim.update_state("sensor.pv_grid_return_power", "25")
    assert pv_sim.service_calls == []


# ── OFF trigger: downward crossings ───────────────────────────────────────────

def test_turn_off_when_surplus_crosses_below_hysteresis(pv_sim: AutomationSimulator):
    """Outlet on, sensor at 20 W → drops to 10 W: crosses below 15 W → turn_off fires."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "10")
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]


def test_no_turn_off_at_exactly_hysteresis_threshold(pv_sim: AutomationSimulator):
    """20 W → 15 W: value equals hysteresis threshold exactly, does NOT cross below → no trigger."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "15")
    assert pv_sim.service_calls == []


def test_no_turn_off_when_surplus_above_hysteresis(pv_sim: AutomationSimulator):
    """20 W → 16 W: still above 15 W hysteresis threshold → outlet stays on, no call."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "16")
    assert pv_sim.service_calls == []


def test_no_turn_off_when_outlet_already_off(pv_sim: AutomationSimulator):
    """
    State guard: outlet already off → condition blocks turn_off from firing again.

    This matters when sensor stays low and multiple updates arrive.
    """
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    # outlet is already "off" (the fixture default)
    pv_sim.update_state("sensor.pv_grid_return_power", "5")
    assert pv_sim.service_calls == []


# ── Hysteresis band: transitions within the dead zone ────────────────────────

def test_no_action_while_sensor_oscillates_in_hysteresis_band(pv_sim: AutomationSimulator):
    """
    Outlet is on, sensor fluctuates anywhere in the dead zone [15 W, 25 W]: no state change.

    Values in this range cross neither the ON threshold (>25) nor the OFF
    threshold (<15), so neither automation fires.
    """
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "25")

    for watts in ["17", "21", "15", "24", "25"]:
        pv_sim.update_state("sensor.pv_grid_return_power", watts)

    assert pv_sim.service_calls == []


def test_no_action_while_outlet_off_sensor_stays_below_on_threshold(pv_sim: AutomationSimulator):
    """Outlet is off, sensor fluctuates between 5 W and 25 W (never strictly above 25): stays off."""
    for watts in ["5", "12", "20", "25", "18"]:
        pv_sim.update_state("sensor.pv_grid_return_power", watts)
    assert pv_sim.service_calls == []


# ── Full ON → OFF → ON state cycles ──────────────────────────────────────────

def test_full_on_off_cycle(pv_sim: AutomationSimulator):
    """
    Complete lifecycle: surplus rises, outlet turns on; surplus drops, outlet turns off.

    State sequence:
      0 W  → 30 W : crosses above 25 W → turn_on
      30 W → 8 W  : crosses below 15 W → turn_off
    """
    pv_sim.update_state("sensor.pv_grid_return_power", "30")
    assert pv_sim.get_state("switch.smart_outlet_1") == "on"

    pv_sim.update_state("sensor.pv_grid_return_power", "8")
    assert pv_sim.get_state("switch.smart_outlet_1") == "off"

    assert len(pv_sim.service_calls) == 2
    assert pv_sim.service_calls[0] == ServiceCall("switch.turn_on", ["switch.smart_outlet_1"])
    assert pv_sim.service_calls[1] == ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])


def test_repeated_on_off_cycles(pv_sim: AutomationSimulator):
    """
    Outlet toggles ON then OFF twice — verifies state guards keep firing correctly
    across multiple full cycles without getting stuck.
    """
    pv_sim.update_state("sensor.pv_grid_return_power", "30")  # turn on
    pv_sim.update_state("sensor.pv_grid_return_power", "8")   # turn off
    pv_sim.update_state("sensor.pv_grid_return_power", "26")  # turn on again
    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # turn off again

    assert len(pv_sim.service_calls) == 4
    assert [c.service for c in pv_sim.service_calls] == [
        "switch.turn_on",
        "switch.turn_off",
        "switch.turn_on",
        "switch.turn_off",
    ]


# ── Sensor edge cases ─────────────────────────────────────────────────────────

def test_no_action_when_sensor_state_is_unavailable(pv_sim: AutomationSimulator):
    """Non-numeric sensor state (unavailable/unknown) does not fire numeric_state trigger."""
    pv_sim.update_state("sensor.pv_grid_return_power", "unavailable")
    assert pv_sim.service_calls == []


def test_turn_off_when_sensor_drops_to_zero(pv_sim: AutomationSimulator):
    """Sensor was at 30 W (outlet on), drops to 0 W → crosses below 15 W → turn_off fires."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "30")
    pv_sim.update_state("sensor.pv_grid_return_power", "0")
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]


def test_turn_off_on_negative_surplus(pv_sim: AutomationSimulator):
    """
    Negative values mean the house is importing power (night / heavy load).
    They cross below 15 W → turn_off fires.
    """
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "-50")
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]
