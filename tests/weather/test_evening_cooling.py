"""Weather group — evening cooling threshold template.

Finds the first hour of the final consecutive cool run in the evening
(i.e. 'when does it stay below the threshold').
Renders nothing if the temperature never drops below the threshold.
"""
from datetime import datetime

TEMPLATE = "weather/evening_cooling.jinja"

# Base forecast for 2026-03-27, evening hours only (UTC = local in tests)
# Threshold default = 21 °C, evening_start default = 18
FORECAST_COOLS_AT_20 = [
    {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 22.0},
    {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 21.5},
    {"datetime": "2026-03-27T20:00:00+00:00", "temperature": 20.5},  # ← first cool
    {"datetime": "2026-03-27T21:00:00+00:00", "temperature": 19.0},
    {"datetime": "2026-03-27T22:00:00+00:00", "temperature": 18.0},
]


def test_cools_during_evening(render):
    """Temperature drops below threshold at 20:00 and stays there."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": FORECAST_COOLS_AT_20},
    )
    assert result == "Ab 20 Uhr bleibt es unter 21 Grad."


def test_never_cools(render):
    """Temperature stays at or above threshold all evening — render nothing."""
    forecast = [
        {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 22.0},
        {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 21.5},
        {"datetime": "2026-03-27T20:00:00+00:00", "temperature": 21.0},  # exactly threshold
        {"datetime": "2026-03-27T21:00:00+00:00", "temperature": 22.0},
        {"datetime": "2026-03-27T22:00:00+00:00", "temperature": 21.0},
    ]
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": forecast},
    )
    assert result == ""


def test_already_cool_at_evening_start(render):
    """All evening entries below threshold → reports evening_start hour."""
    forecast = [
        {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 20.5},
        {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 19.0},
        {"datetime": "2026-03-27T20:00:00+00:00", "temperature": 18.0},
    ]
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": forecast},
    )
    assert result == "Ab 18 Uhr bleibt es unter 21 Grad."


def test_dips_then_rises_then_stays_cool(render):
    """Temp dips below, rises again, then cools for good — reports second cool start."""
    forecast = [
        {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 22.0},
        {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 20.0},  # first dip
        {"datetime": "2026-03-27T20:00:00+00:00", "temperature": 21.5},  # rises back
        {"datetime": "2026-03-27T21:00:00+00:00", "temperature": 20.0},  # cools for good
        {"datetime": "2026-03-27T22:00:00+00:00", "temperature": 19.0},
    ]
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": forecast},
    )
    assert result == "Ab 21 Uhr bleibt es unter 21 Grad."


def test_custom_threshold(render):
    """Custom threshold of 19 °C — cool only at the last hour."""
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": FORECAST_COOLS_AT_20, "temperature_threshold": 19},
    )
    assert result == "Ab 22 Uhr bleibt es unter 19 Grad."


def test_custom_evening_start(render):
    """Custom evening_start=20 ignores entries before 20:00."""
    forecast = [
        {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 20.0},  # ignored
        {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 20.0},  # ignored
        {"datetime": "2026-03-27T20:00:00+00:00", "temperature": 20.0},  # first in window
        {"datetime": "2026-03-27T21:00:00+00:00", "temperature": 19.0},
    ]
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": forecast, "evening_start": 20},
    )
    assert result == "Ab 20 Uhr bleibt es unter 21 Grad."


def test_tomorrow_forecast_ignored(render):
    """Cool entries from tomorrow do not trigger output for today."""
    forecast = [
        {"datetime": "2026-03-27T18:00:00+00:00", "temperature": 22.0},
        {"datetime": "2026-03-27T19:00:00+00:00", "temperature": 21.5},
        {"datetime": "2026-03-28T18:00:00+00:00", "temperature": 17.0},  # tomorrow
        {"datetime": "2026-03-28T19:00:00+00:00", "temperature": 16.0},  # tomorrow
    ]
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 8, 0, 0),
        variables={"forecast": forecast},
    )
    assert result == ""
