"""Shared fixtures: a Jinja2 environment that mimics Home Assistant's template engine."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import jinja2
import jinja2.sandbox
import pytest

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class _State:
    """Minimal HA state object for use in tests (mirrors HA's State class)."""

    def __init__(self, entity_id: str, state: str, attributes: dict | None = None):
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}
        self.name = self.attributes.get("friendly_name", entity_id)


class _StatesProxy:
    """Mimics HA's `states` global: callable for single entity lookup AND
    attribute access for domain iteration (e.g. `states.sensor`)."""

    def __init__(self, states_dict: dict, state_objects: list[_State]):
        self._states = states_dict
        # Group state objects by domain (the part before the first dot)
        self._domains: dict[str, list[_State]] = {}
        for obj in state_objects:
            domain = obj.entity_id.split(".")[0]
            self._domains.setdefault(domain, []).append(obj)

    def __call__(self, entity_id: str) -> str:
        return self._states.get(entity_id, "unknown")

    def __getattr__(self, domain: str) -> list[_State]:
        # Only called for attributes not found via normal lookup
        return self._domains.get(domain, [])


def make_environment(
    *,
    states: dict[str, str] | None = None,
    attributes: dict[str, dict] | None = None,
    now: datetime | None = None,
    state_objects: list[_State] | None = None,
    labels: dict[str, list[str]] | None = None,
) -> jinja2.Environment:
    """Return a Jinja2 env with HA globals and filters stubbed out."""
    _states = states or {}
    _attributes = attributes or {}
    _now = now or datetime(2026, 1, 1, 8, 0, 0)

    env = jinja2.sandbox.ImmutableSandboxedEnvironment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=jinja2.Undefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # ── HA global functions ──────────────────────────────────────────────────
    env.globals["states"] = _StatesProxy(_states, state_objects or [])
    env.globals["is_state"] = lambda entity_id, state: _states.get(entity_id) == state
    env.globals["state_attr"] = (
        lambda entity_id, attr: _attributes.get(entity_id, {}).get(attr)
    )
    env.globals["now"] = lambda: _now
    env.globals["utcnow"] = lambda: _now
    env.globals["today_at"] = lambda t="00:00": datetime.combine(
        _now.date(), datetime.strptime(t, "%H:%M").time()
    )
    env.globals["as_timestamp"] = (
        lambda dt: dt.timestamp() if hasattr(dt, "timestamp") else float(dt)
    )
    def _as_datetime(value):
        """Mirror HA's as_datetime: return datetime objects as-is, parse strings."""
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    env.globals["as_datetime"] = _as_datetime
    env.filters["as_datetime"] = _as_datetime
    _labels = labels or {}
    env.globals["label_entities"] = lambda label: _labels.get(label, [])

    # ── HA filters (override Jinja2 defaults to support default args) ────────
    env.filters["float"] = lambda value, default=0.0: (
        float(value)
        if value not in (None, "unknown", "unavailable", "")
        else float(default)
    )
    env.filters["int"] = lambda value, default=0: (
        int(float(value))
        if value not in (None, "unknown", "unavailable", "")
        else int(default)
    )

    return env


@pytest.fixture
def render():
    """Render helper: render(template_path, states={}, attributes={}, now=dt, variables={}, state_objects=[])."""

    def _render(
        template_path: str,
        *,
        states: dict[str, str] | None = None,
        attributes: dict[str, dict] | None = None,
        now: datetime | None = None,
        variables: dict | None = None,
        state_objects: list[_State] | None = None,
        labels: dict[str, list[str]] | None = None,
    ) -> str:
        env = make_environment(
            states=states,
            attributes=attributes,
            now=now,
            state_objects=state_objects,
            labels=labels,
        )
        tmpl = env.get_template(template_path)
        return tmpl.render(**(variables or {})).strip()

    return _render
