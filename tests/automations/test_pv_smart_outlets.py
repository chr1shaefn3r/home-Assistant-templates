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
    """Outlet on, sensor at 20 W → drops to 10 W and stays there for 30 min → turn_off fires."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "10")  # starts 30-min timer
    pv_sim.advance_time(30)
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
    Complete lifecycle: surplus rises, outlet turns on; surplus drops and stays low, outlet turns off.

    State sequence:
      0 W  → 30 W : crosses above 25 W → turn_on (immediate)
      30 W → 8 W  : crosses below 15 W → starts 30-min timer
      +30 min      : timer fires → turn_off
    """
    pv_sim.update_state("sensor.pv_grid_return_power", "30")
    assert pv_sim.get_state("switch.smart_outlet_1") == "on"

    pv_sim.update_state("sensor.pv_grid_return_power", "8")   # starts timer
    pv_sim.advance_time(30)                                    # timer fires
    assert pv_sim.get_state("switch.smart_outlet_1") == "off"

    assert len(pv_sim.service_calls) == 2
    assert pv_sim.service_calls[0] == ServiceCall("switch.turn_on", ["switch.smart_outlet_1"])
    assert pv_sim.service_calls[1] == ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])


def test_repeated_on_off_cycles(pv_sim: AutomationSimulator):
    """
    Outlet toggles ON then OFF twice — verifies state guards keep firing correctly
    across multiple full cycles without getting stuck.
    """
    pv_sim.update_state("sensor.pv_grid_return_power", "30")  # turn on (immediate)
    pv_sim.update_state("sensor.pv_grid_return_power", "8")   # start off-timer
    pv_sim.advance_time(30)                                    # off-timer fires
    pv_sim.update_state("sensor.pv_grid_return_power", "26")  # turn on again (immediate)
    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # start off-timer again
    pv_sim.advance_time(30)                                    # off-timer fires again

    assert len(pv_sim.service_calls) == 4
    assert [c.service for c in pv_sim.service_calls] == [
        "switch.turn_on",
        "switch.turn_off",
        "switch.turn_on",
        "switch.turn_off",
    ]


# ── Minimum run-time (new requirement) ───────────────────────────────────────

def test_outlet_not_turned_off_before_min_run_time(pv_sim: AutomationSimulator):
    """Surplus drops below the OFF threshold — outlet must stay on until min_on_minutes elapses."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "30")
    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # crosses below 15 W
    assert pv_sim.service_calls == []                          # must NOT fire immediately


def test_outlet_turns_off_after_min_run_time_elapses(pv_sim: AutomationSimulator):
    """Surplus stays below threshold for 30+ min → turn_off fires."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "30")
    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # crosses below 15 W
    pv_sim.advance_time(30)                                    # 30 minutes elapse
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]


def test_min_run_time_timer_resets_if_surplus_recovers(pv_sim: AutomationSimulator):
    """
    Surplus drops, recovers before 30 min, then drops again — clock restarts on each new crossing.

    Timeline:
      t=0   surplus drops to 5 W  → timer starts
      t=15  surplus recovers to 20 W → timer cancelled
      t=30  (only 15 min since last drop) — no turn_off
      t=30  surplus drops to 5 W again → new timer starts
      t=60  30 min after second drop → turn_off fires
    """
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "30")

    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # t=0  timer starts
    pv_sim.advance_time(15)                                    # t=15 — not yet
    pv_sim.update_state("sensor.pv_grid_return_power", "20")  # t=15 surplus recovers → cancel
    pv_sim.advance_time(15)                                    # t=30 — still no fire (timer was reset)
    assert pv_sim.service_calls == []

    pv_sim.update_state("sensor.pv_grid_return_power", "5")   # t=30 new crossing → new timer
    pv_sim.advance_time(30)                                    # t=60 — 30 min since second drop
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]


# ── Sensor edge cases ─────────────────────────────────────────────────────────

def test_no_action_when_sensor_state_is_unavailable(pv_sim: AutomationSimulator):
    """Non-numeric sensor state (unavailable/unknown) does not fire numeric_state trigger."""
    pv_sim.update_state("sensor.pv_grid_return_power", "unavailable")
    assert pv_sim.service_calls == []


def test_turn_off_when_sensor_drops_to_zero(pv_sim: AutomationSimulator):
    """Sensor was at 30 W (outlet on), drops to 0 W and stays there for 30 min → turn_off fires."""
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "30")
    pv_sim.update_state("sensor.pv_grid_return_power", "0")   # starts timer
    pv_sim.advance_time(30)
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]


def test_turn_off_on_negative_surplus(pv_sim: AutomationSimulator):
    """
    Negative values mean the house is importing power (night / heavy load).
    They cross below 15 W and after 30 min → turn_off fires.
    """
    pv_sim.set_state("switch.smart_outlet_1", "on")
    pv_sim.set_state("sensor.pv_grid_return_power", "20")
    pv_sim.update_state("sensor.pv_grid_return_power", "-50")  # starts timer
    pv_sim.advance_time(30)
    assert pv_sim.service_calls == [
        ServiceCall("switch.turn_off", ["switch.smart_outlet_1"])
    ]
