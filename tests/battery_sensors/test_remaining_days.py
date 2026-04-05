"""Battery sensors group — remaining runtime estimation via input_datetime helpers.

Naming convention: input_datetime.{entity_suffix}_replaced
Example: sensor.motion_battery → input_datetime.motion_battery_replaced

Formula:
  days_since      = (now - replaced_date).total_seconds() / 86400
  capacity_used   = 100 - current_level
  daily_drain     = capacity_used / days_since
  days_remaining  = current_level / daily_drain  (rounded to int)

Guards:
  - Helper missing or unavailable → no estimate shown
  - days_since < 1  → too recent, no estimate
  - capacity_used == 0 → would divide by zero, no estimate
"""
from datetime import datetime

from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

MOTION = _State(
    "sensor.motion_battery",
    "10",
    {"device_class": "battery", "friendly_name": "Bewegungsmelder"},
)


def test_remaining_days_shown_when_helper_present(render):
    """90 days since replacement, used 90%, 10% left → daily_drain=1.0 → ~10 Tage."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 0, 0, 0),
        state_objects=[MOTION],
        states={"input_datetime.motion_battery_replaced": "2025-12-27"},
    )
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%, ~10 Tage)"


def test_remaining_days_with_battery_type(render):
    """Type label and remaining days both appear."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 0, 0, 0),
        state_objects=[MOTION],
        states={"input_datetime.motion_battery_replaced": "2025-12-27"},
        labels={"battery_cr2032": ["sensor.motion_battery"]},
    )
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%, CR2032, ~10 Tage)"


def test_no_estimate_when_helper_missing(render):
    """No input_datetime helper → format unchanged (no Tage)."""
    result = render(
        TEMPLATE,
        state_objects=[MOTION],
    )
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%)"


def test_no_estimate_when_helper_unavailable(render):
    """Helper present but state is 'unavailable' → no estimate."""
    result = render(
        TEMPLATE,
        state_objects=[MOTION],
        states={"input_datetime.motion_battery_replaced": "unavailable"},
    )
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%)"


def test_no_estimate_when_replaced_too_recently(render):
    """Replaced less than 1 day ago → no meaningful drain rate yet."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 12, 0, 0),
        state_objects=[MOTION],
        states={"input_datetime.motion_battery_replaced": "2026-03-27"},
    )
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%)"


def test_no_estimate_when_full_at_replacement(render):
    """Sensor still at 100% → capacity_used=0, would divide by zero → no estimate."""
    full = _State(
        "sensor.motion_battery",
        "15",
        {"device_class": "battery", "friendly_name": "Bewegungsmelder"},
    )
    # If the helper says it was replaced 90 days ago but somehow capacity_used would
    # be 85, that's fine. Test the actual zero case: sensor at exactly 100%.
    full_sensor = _State(
        "sensor.motion_battery",
        "100",
        {"device_class": "battery", "friendly_name": "Bewegungsmelder"},
    )
    # 100% is above threshold — use threshold=100 to force it into the low list
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 0, 0, 0),
        state_objects=[full_sensor],
        states={"input_datetime.motion_battery_replaced": "2025-12-27"},
        variables={"threshold": 100},
    )
    # capacity_used = 100 - 100 = 0 → no estimate
    assert "Tage" not in result
