"""Lightweight Home Assistant automation simulator for unit testing.

This module provides AutomationSimulator — a pure-Python class that parses a
YAML automation file, simulates state changes, evaluates trigger/condition/
action pipelines, and records service calls for assertion.

Supported YAML constructs
─────────────────────────
Triggers:
  - platform: numeric_state
      entity_id: <str>
      above: <number | "{{ expr }}">   # fires on upward crossing
      below: <number | "{{ expr }}">   # fires on downward crossing
      for:                             # optional: condition must hold for this duration
        minutes: <number | "{{ expr }}">
        hours:   <number | "{{ expr }}">   # optional
        seconds: <number | "{{ expr }}">   # optional

Conditions (all must pass; empty list = always passes):
  - condition: state
      entity_id: <str>
      state: <str>

Actions (executed in order):
  - service: <domain.service>          # switch.turn_on / switch.turn_off
      target:
        entity_id: <str | list[str]>

State side-effects:
  switch.turn_on  → entity state set to "on"
  switch.turn_off → entity state set to "off"

Time simulation
───────────────
Triggers with a 'for:' clause are held in a pending queue.  Use
advance_time(minutes) to move the simulator clock forward; any pending
trigger whose 'for:' duration has elapsed will fire at that point.  If
the watched entity's value returns to the non-trigger side before the
duration elapses, the pending trigger is automatically cancelled.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ServiceCall:
    """A recorded service invocation."""
    service: str            # e.g. "switch.turn_on"
    entity_ids: list[str]   # target entities (always a list)


@dataclass
class _PendingTrigger:
    """A trigger with a 'for:' clause that has not yet elapsed."""
    automation: dict
    trigger: dict
    for_minutes: float
    activated_at: float     # simulator clock value (minutes) when the crossing was detected


class AutomationSimulator:
    """
    Simulates the trigger → condition → action pipeline of HA automations.

    Usage
    ─────
    sim = AutomationSimulator("automations/pv_smart_outlets.yaml")
    sim.set_state("sensor.pv_grid_return_power", "0")
    sim.set_state("switch.smart_outlet_1", "off")

    # Immediate trigger (no 'for:')
    sim.update_state("sensor.pv_grid_return_power", "30")
    assert sim.service_calls == [ServiceCall("switch.turn_on", ["switch.smart_outlet_1"])]

    # Deferred trigger (with 'for:')
    sim.update_state("sensor.pv_grid_return_power", "5")   # starts 30-min timer
    assert sim.service_calls == [...]                       # turn_on only, not yet off
    sim.advance_time(30)                                    # clock advances 30 minutes
    assert sim.service_calls[-1] == ServiceCall("switch.turn_off", [...])
    """

    def __init__(self, yaml_path: str | Path) -> None:
        self._automations: list[dict[str, Any]] = yaml.safe_load(
            Path(yaml_path).read_text()
        )
        self._states: dict[str, str] = {}
        self.service_calls: list[ServiceCall] = []
        self._time_minutes: float = 0.0
        self._pending: list[_PendingTrigger] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def set_state(self, entity_id: str, state: str) -> None:
        """Set initial state without triggering any automations."""
        self._states[entity_id] = state

    def get_state(self, entity_id: str) -> str:
        """Return current state string, or 'unknown' if not set."""
        return self._states.get(entity_id, "unknown")

    def update_state(self, entity_id: str, new_state: str) -> None:
        """
        Update state and evaluate all automations whose trigger watches this entity.

        Triggers without 'for:' fire immediately on a crossing.
        Triggers with 'for:' are queued; call advance_time() to mature them.
        A pending trigger is cancelled if the entity's value returns to the
        non-trigger side before the duration elapses.
        """
        old_state = self._states.get(entity_id, "unknown")
        self._states[entity_id] = new_state

        # Cancel any pending triggers whose level condition is no longer met
        self._cancel_stale_pending(entity_id, new_state)

        for automation in self._automations:
            triggers = automation.get("trigger", [])
            if not isinstance(triggers, list):
                triggers = [triggers]

            for trigger in triggers:
                if not self._trigger_fires(trigger, entity_id, old_state, new_state, automation):
                    continue

                for_raw = trigger.get("for")
                if for_raw is not None:
                    variables = automation.get("variables", {})
                    for_minutes = self._resolve_for_minutes(for_raw, variables)
                    # Reset any existing pending timer for this automation (new crossing wins)
                    self._pending = [p for p in self._pending if p.automation is not automation]
                    self._pending.append(_PendingTrigger(
                        automation=automation,
                        trigger=trigger,
                        for_minutes=for_minutes,
                        activated_at=self._time_minutes,
                    ))
                else:
                    if self._conditions_pass(automation.get("condition", [])):
                        self._execute_actions(automation.get("action", []))
                break  # each automation fires at most once per update

    def advance_time(self, minutes: float) -> None:
        """
        Advance the simulator clock by the given number of minutes.

        Any pending 'for:' trigger whose duration has now elapsed is evaluated:
        its conditions are checked and, if they pass, its actions are executed.
        """
        self._time_minutes += minutes
        matured = [
            p for p in self._pending
            if self._time_minutes - p.activated_at >= p.for_minutes
        ]
        self._pending = [
            p for p in self._pending
            if self._time_minutes - p.activated_at < p.for_minutes
        ]
        for p in matured:
            if self._conditions_pass(p.automation.get("condition", [])):
                self._execute_actions(p.automation.get("action", []))

    def clear_service_calls(self) -> None:
        """Reset the recorded call list between test phases."""
        self.service_calls = []

    # ── Private: pending trigger management ──────────────────────────────────

    def _cancel_stale_pending(self, entity_id: str, new_state: str) -> None:
        """Remove pending triggers whose level condition is no longer satisfied."""
        try:
            val = float(new_state)
        except (ValueError, TypeError):
            return  # non-numeric state: leave pending triggers as-is

        remaining = []
        for pt in self._pending:
            if pt.trigger.get("entity_id") != entity_id:
                remaining.append(pt)
                continue
            variables = pt.automation.get("variables", {})
            below_raw = pt.trigger.get("below")
            above_raw = pt.trigger.get("above")
            # Cancel if the value has crossed back to the non-trigger side
            if below_raw is not None and val >= self._resolve_numeric(below_raw, variables):
                continue  # cancelled
            if above_raw is not None and val <= self._resolve_numeric(above_raw, variables):
                continue  # cancelled
            remaining.append(pt)
        self._pending = remaining

    # ── Private: trigger evaluation ───────────────────────────────────────────

    def _trigger_fires(
        self,
        trigger: dict,
        changed_entity: str,
        old_state: str,
        new_state: str,
        automation: dict,
    ) -> bool:
        if trigger.get("platform") != "numeric_state":
            return False
        if trigger.get("entity_id") != changed_entity:
            return False

        try:
            old_val = float(old_state)
            new_val = float(new_state)
        except (ValueError, TypeError):
            return False  # non-numeric states never fire numeric_state triggers

        variables = automation.get("variables", {})

        above_raw = trigger.get("above")
        if above_raw is not None:
            threshold = self._resolve_numeric(above_raw, variables)
            # HA semantics: fires when crossing from <= threshold to > threshold
            if old_val <= threshold < new_val:
                return True

        below_raw = trigger.get("below")
        if below_raw is not None:
            threshold = self._resolve_numeric(below_raw, variables)
            # HA semantics: fires when crossing from >= threshold to < threshold
            if old_val >= threshold > new_val:
                return True

        return False

    def _resolve_numeric(self, value: Any, variables: dict[str, Any]) -> float:
        """
        Resolve a trigger threshold that may be a literal number or a
        Jinja-style template string referencing automation variables.

        Supported template forms:
          "{{ outlet_watts }}"
          "{{ (outlet_watts * hysteresis_factor) | int }}"
          "{{ outlet_watts + hysteresis_watts }}"

        The expression is validated against a strict whitelist (digits,
        whitespace, arithmetic operators) before eval to prevent injection.
        """
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            inner = value.strip()
            # Strip {{ }} wrapper
            if inner.startswith("{{") and inner.endswith("}}"):
                inner = inner[2:-2].strip()
            # Strip outer parentheses introduced by e.g. (expr) | int
            inner = re.sub(r'^\((.+)\)$', r'\1', inner.strip())
            # Strip | int or | float filter suffix
            inner = re.sub(r'\|\s*(int|float)\s*$', '', inner).strip()
            # Substitute variable names with their numeric values
            for var_name, var_val in variables.items():
                inner = re.sub(rf'\b{re.escape(var_name)}\b', str(var_val), inner)
            # Validate: only digits, whitespace, decimal points, and basic operators
            if re.fullmatch(r'[\d\s.\+\-\*\/\(\)]+', inner):
                return float(eval(inner))  # noqa: S307 — input validated by regex above
        raise ValueError(f"Cannot resolve threshold: {value!r}")

    def _resolve_for_minutes(self, for_val: Any, variables: dict[str, Any]) -> float:
        """
        Return the 'for:' duration in minutes.

        Accepts:
          for: {minutes: 30}
          for: {minutes: "{{ min_on_minutes }}"}
          for: {hours: 1, minutes: 30}
          for: "01:30:00"   (HH:MM:SS string)
        """
        if isinstance(for_val, dict):
            hours   = self._resolve_numeric(for_val.get("hours",   0), variables)
            minutes = self._resolve_numeric(for_val.get("minutes", 0), variables)
            seconds = self._resolve_numeric(for_val.get("seconds", 0), variables)
            return hours * 60.0 + minutes + seconds / 60.0
        if isinstance(for_val, str):
            parts = for_val.strip().split(":")
            if len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        raise ValueError(f"Cannot resolve 'for:' duration: {for_val!r}")

    # ── Private: condition evaluation ─────────────────────────────────────────

    def _conditions_pass(self, conditions: list[dict] | dict) -> bool:
        if not conditions:
            return True
        if isinstance(conditions, dict):
            conditions = [conditions]
        return all(self._condition_passes(c) for c in conditions)

    def _condition_passes(self, condition: dict) -> bool:
        if condition.get("condition") == "state":
            return self._states.get(condition["entity_id"], "unknown") == condition["state"]
        return False  # unknown condition type: fail safe (do not fire)

    # ── Private: action execution ─────────────────────────────────────────────

    def _execute_actions(self, actions: list[dict] | dict) -> None:
        if isinstance(actions, dict):
            actions = [actions]
        for action in actions:
            self._execute_action(action)

    def _execute_action(self, action: dict) -> None:
        service = action.get("service", "")
        target = action.get("target", {})
        raw_entity = target.get("entity_id", [])
        entity_ids = [raw_entity] if isinstance(raw_entity, str) else list(raw_entity)

        self.service_calls.append(ServiceCall(service=service, entity_ids=entity_ids))

        # Apply state side-effects so subsequent conditions see updated state
        for eid in entity_ids:
            if service == "switch.turn_on":
                self._states[eid] = "on"
            elif service == "switch.turn_off":
                self._states[eid] = "off"
