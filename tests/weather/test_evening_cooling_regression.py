"""Regression test for the real-world forecast reported on 2026-04-12.

Root cause: some HA weather integrations provide `datetime` as a Python
datetime object rather than an ISO 8601 string.  The template used
`slot.datetime[:10]` (string slicing) for the date check, which raises
TypeError when the value is a datetime object.  HA catches the exception
and returns an empty string.

The fix replaces `slot.datetime[:10]` with
`(slot.datetime | as_datetime).date() | string`, which works for
both strings and datetime objects (HA's `as_datetime` returns objects
as-is; our conftest stub does the same).
"""
from datetime import datetime, timezone

TEMPLATE = "weather/evening_cooling.jinja"

UTC = timezone.utc

# Exact data from the user's HA instance on 2026-04-12 –
# presented here as Python datetime objects (the form some
# integrations expose in the template context).
FORECAST_AS_OBJECTS = [
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 17, 0, tzinfo=UTC), "temperature": 11.5},
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 18, 0, tzinfo=UTC), "temperature": 10.8},
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 19, 0, tzinfo=UTC), "temperature": 10.5},
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 20, 0, tzinfo=UTC), "temperature": 10.3},
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 21, 0, tzinfo=UTC), "temperature": 10.1},
    {"condition": "cloudy", "datetime": datetime(2026, 4, 12, 22, 0, tzinfo=UTC), "temperature":  9.9},
    {"condition": "rainy",  "datetime": datetime(2026, 4, 12, 23, 0, tzinfo=UTC), "temperature":  9.6},
    {"condition": "rainy",  "datetime": datetime(2026, 4, 13,  0, 0, tzinfo=UTC), "temperature":  9.5},
]

# Same data as ISO strings (the alternative form; both must work).
FORECAST_AS_STRINGS = [
    {"condition": "cloudy", "datetime": "2026-04-12T17:00:00+00:00", "temperature": 11.5},
    {"condition": "cloudy", "datetime": "2026-04-12T18:00:00+00:00", "temperature": 10.8},
    {"condition": "cloudy", "datetime": "2026-04-12T19:00:00+00:00", "temperature": 10.5},
    {"condition": "cloudy", "datetime": "2026-04-12T20:00:00+00:00", "temperature": 10.3},
    {"condition": "cloudy", "datetime": "2026-04-12T21:00:00+00:00", "temperature": 10.1},
    {"condition": "cloudy", "datetime": "2026-04-12T22:00:00+00:00", "temperature":  9.9},
    {"condition": "rainy",  "datetime": "2026-04-12T23:00:00+00:00", "temperature":  9.6},
    {"condition": "rainy",  "datetime": "2026-04-13T00:00:00+00:00", "temperature":  9.5},
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
