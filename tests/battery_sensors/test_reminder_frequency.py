"""Battery sensors group — how often a low battery is reported.

The template renders once per day, so the reminder schedule is derived from
the date and the estimated remaining runtime (see test_remaining_days.py):

  - ≤ 7 days left   → reported every day
  - 8–14 days left  → reported every other day (days with an even date ordinal)
  - > 14 days left  → reported once a week, on `weekly_reminder_weekday`
                      (ISO weekday, 1 = Monday … 7 = Sunday, default 6 = Saturday)
  - no estimate     → reported every day (no runtime to go on)

Test week: Mon 2026-03-23 … Sun 2026-03-29.
Even ordinals in that week: Mon 23, Wed 25, Fri 27, Sun 29.
"""
from datetime import datetime, timedelta

import pytest

from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

# With a 10 % level the template estimates days_remaining = days_since / 9.
MOTION = _State("sensor.motion_battery", "10", {"device_class": "battery", "friendly_name": "Bewegungsmelder"})
DOOR   = _State("sensor.door_battery",   "10", {"device_class": "battery", "friendly_name": "Türsensor"})

WEEK = [datetime(2026, 3, d, 6, 0, 0) for d in range(23, 30)]
EVEN_DAYS = [datetime(2026, 3, d, 6, 0, 0) for d in (23, 25, 27, 29)]
ODD_DAYS = [datetime(2026, 3, d, 6, 0, 0) for d in (24, 26, 28)]
SATURDAY = datetime(2026, 3, 28, 6, 0, 0)
NOT_SATURDAY = [day for day in WEEK if day != SATURDAY]


def replaced_for(now: datetime, days_remaining: int) -> str:
    """Replacement date that yields `days_remaining` for a sensor at 10 %."""
    return (now - timedelta(days=days_remaining * 9)).date().isoformat()


def render_motion(render, now: datetime, days_remaining: int, **kwargs) -> str:
    return render(
        TEMPLATE,
        now=now,
        state_objects=[MOTION],
        states={"input_datetime.motion_battery_replaced": replaced_for(now, days_remaining)},
        **kwargs,
    )


def expected(days_remaining: int) -> str:
    return f"Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (ungefähr {days_remaining} Tage)"


# ── Last week: daily ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("now", WEEK, ids=lambda d: d.strftime("%a"))
@pytest.mark.parametrize("days_remaining", [1, 5, 7])
def test_last_week_reported_every_day(render, now, days_remaining):
    assert render_motion(render, now, days_remaining) == expected(days_remaining)


# ── Second-to-last week: every other day ─────────────────────────────────────

@pytest.mark.parametrize("now", EVEN_DAYS, ids=lambda d: d.strftime("%a"))
@pytest.mark.parametrize("days_remaining", [8, 14])
def test_second_week_reported_on_even_days(render, now, days_remaining):
    assert render_motion(render, now, days_remaining) == expected(days_remaining)


@pytest.mark.parametrize("now", ODD_DAYS, ids=lambda d: d.strftime("%a"))
@pytest.mark.parametrize("days_remaining", [8, 14])
def test_second_week_silent_on_odd_days(render, now, days_remaining):
    assert render_motion(render, now, days_remaining) == ""


# ── More than two weeks: weekly ───────────────────────────────────────────────

@pytest.mark.parametrize("days_remaining", [15, 30])
def test_more_than_two_weeks_reported_on_saturday(render, days_remaining):
    assert render_motion(render, SATURDAY, days_remaining) == expected(days_remaining)


@pytest.mark.parametrize("now", NOT_SATURDAY, ids=lambda d: d.strftime("%a"))
@pytest.mark.parametrize("days_remaining", [15, 30])
def test_more_than_two_weeks_silent_on_other_days(render, now, days_remaining):
    assert render_motion(render, now, days_remaining) == ""


def test_custom_weekly_reminder_weekday(render):
    """weekly_reminder_weekday=1 moves the weekly reminder to Monday."""
    monday = datetime(2026, 3, 23, 6, 0, 0)
    assert render_motion(render, monday, 20, variables={"weekly_reminder_weekday": 1}) == expected(20)
    assert render_motion(render, SATURDAY, 20, variables={"weekly_reminder_weekday": 1}) == ""


# ── No runtime estimate: daily ────────────────────────────────────────────────

@pytest.mark.parametrize("now", WEEK, ids=lambda d: d.strftime("%a"))
def test_without_estimate_reported_every_day(render, now):
    result = render(TEMPLATE, now=now, state_objects=[MOTION])
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (10%)"


# ── Several devices: each follows its own schedule ────────────────────────────

def test_only_devices_due_today_are_listed(render):
    """Tuesday (odd, not Saturday): the 5-day device is due, the 20-day one is not."""
    tuesday = datetime(2026, 3, 24, 6, 0, 0)
    result = render(
        TEMPLATE,
        now=tuesday,
        state_objects=[MOTION, DOOR],
        states={
            "input_datetime.motion_battery_replaced": replaced_for(tuesday, 5),
            "input_datetime.door_battery_replaced": replaced_for(tuesday, 20),
        },
    )
    assert result == expected(5)


def test_several_devices_due_on_saturday(render):
    result = render(
        TEMPLATE,
        now=SATURDAY,
        state_objects=[MOTION, DOOR],
        states={
            "input_datetime.motion_battery_replaced": replaced_for(SATURDAY, 5),
            "input_datetime.door_battery_replaced": replaced_for(SATURDAY, 20),
        },
    )
    assert result == (
        "Folgende Geräte haben niedrigen Akkustand: "
        "Bewegungsmelder (ungefähr 5 Tage), Türsensor (ungefähr 20 Tage)"
    )
