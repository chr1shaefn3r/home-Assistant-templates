"""Regression tests for real-world forecast failures on evening_cooling.

Bug 1 (2026-04-12): some HA weather integrations provide `datetime` as a
Python datetime object rather than an ISO 8601 string.  The template used
`slot.datetime[:10]` (string slicing), which raises TypeError on a datetime
object.  HA silently catches the exception and returns an empty string.

Fix 1: replace `slot.datetime[:10]` with
`(slot.datetime | as_datetime).date() | string`.

Bug 2 (2026-04-12, late evening at 22:25): UTC forecast entries for
"tonight" at 22:00–23:00 UTC correspond to midnight/01:00 in a UTC+2
(CEST) local timezone — i.e. they are *tomorrow* in local time.  Because
the date comparison used the raw UTC date component these entries were
included in today's loop.  If their temperature was ≥ 21 °C (possible for
early-morning forecasts) they triggered the RESET branch, wiping the
`found` flag and producing empty output.

Fix 2: pipe forecast datetimes through `as_local` before extracting the
date and hour, so both `today` (from `now().date()`) and the slot's date
live in the same local timezone.
"""
from datetime import datetime, timedelta, timezone

TEMPLATE = "weather/evening_cooling.jinja"

UTC  = timezone.utc
CEST = timezone(timedelta(hours=2))


# ── Bug 1: datetime objects vs ISO strings ────────────────────────────────────

FORECAST_AS_OBJECTS = [
    {"datetime": datetime(2026, 4, 12, 17, 0, tzinfo=UTC), "temperature": 11.5},
    {"datetime": datetime(2026, 4, 12, 18, 0, tzinfo=UTC), "temperature": 10.8},
    {"datetime": datetime(2026, 4, 12, 19, 0, tzinfo=UTC), "temperature": 10.5},
    {"datetime": datetime(2026, 4, 12, 20, 0, tzinfo=UTC), "temperature": 10.3},
    {"datetime": datetime(2026, 4, 12, 21, 0, tzinfo=UTC), "temperature": 10.1},
    {"datetime": datetime(2026, 4, 12, 22, 0, tzinfo=UTC), "temperature":  9.9},
    {"datetime": datetime(2026, 4, 12, 23, 0, tzinfo=UTC), "temperature":  9.6},
    {"datetime": datetime(2026, 4, 13,  0, 0, tzinfo=UTC), "temperature":  9.5},
]

FORECAST_AS_STRINGS = [
    {"datetime": "2026-04-12T17:00:00+00:00", "temperature": 11.5},
    {"datetime": "2026-04-12T18:00:00+00:00", "temperature": 10.8},
    {"datetime": "2026-04-12T19:00:00+00:00", "temperature": 10.5},
    {"datetime": "2026-04-12T20:00:00+00:00", "temperature": 10.3},
    {"datetime": "2026-04-12T21:00:00+00:00", "temperature": 10.1},
    {"datetime": "2026-04-12T22:00:00+00:00", "temperature":  9.9},
    {"datetime": "2026-04-12T23:00:00+00:00", "temperature":  9.6},
    {"datetime": "2026-04-13T00:00:00+00:00", "temperature":  9.5},
]


def test_datetime_objects_in_forecast(render):
    """Regression: datetime objects (not strings) must work the same as strings."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 4, 12, 8, 0, 0),
        variables={"forecast": FORECAST_AS_OBJECTS},
    )
    assert result == "Ab 18 Uhr bleibt es unter 21 Grad."


def test_iso_strings_in_forecast(render):
    """String datetimes continue to work after the fix."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 4, 12, 8, 0, 0),
        variables={"forecast": FORECAST_AS_STRINGS},
    )
    assert result == "Ab 18 Uhr bleibt es unter 21 Grad."


# ── Bug 2: UTC entries crossing local midnight reset ns.found ─────────────────

# CEST evening hours 21–23 (UTC 19–21) are cool; UTC 22–23 map to CEST
# midnight / 01:00 on April 13 and happen to be warm — they must be excluded.
FORECAST_CROSSES_LOCAL_MIDNIGHT = [
    {"datetime": "2026-04-12T19:00:00+00:00", "temperature": 10.5},  # CEST 21:00 cool
    {"datetime": "2026-04-12T20:00:00+00:00", "temperature": 10.0},  # CEST 22:00 cool
    {"datetime": "2026-04-12T21:00:00+00:00", "temperature":  9.5},  # CEST 23:00 cool
    # These two are UTC April 12 but CEST April 13 — warm, must NOT reset found
    {"datetime": "2026-04-12T22:00:00+00:00", "temperature": 22.0},  # CEST midnight, warm
    {"datetime": "2026-04-12T23:00:00+00:00", "temperature": 23.0},  # CEST 01:00,   warm
]


def test_late_evening_not_reset_by_next_local_day_entry(render):
    """Regression: warm entries that are tomorrow in local time must be excluded.

    Without the fix the UTC 22:00 and 23:00 entries (CEST midnight / 01:00
    on April 13) were included because their UTC date matched today.  Their
    warm temperatures triggered the RESET branch, clearing ns.found and
    producing empty output despite hours 21–23 CEST being cool.
    """
    result = render(
        TEMPLATE,
        now=datetime(2026, 4, 12, 22, 25, 0),
        variables={"forecast": FORECAST_CROSSES_LOCAL_MIDNIGHT},
        local_tz=CEST,
    )
    assert result == "Ab 21 Uhr bleibt es unter 21 Grad."
