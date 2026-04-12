"""Integration test — greeting_day_summary composes all template groups.

Happy-path scenario: every included template produces visible output.
  - greeting             → time-of-day greeting
  - daily_weather_summary → weather condition + high temperature
  - daily_rain_summary   → rain window during the day
  - evening_cooling      → hour when temperature stays below threshold
  - daily_family_summary → upcoming calendar event
  - low_battery_summary  → low-battery sensor alert
"""
from datetime import datetime

from tests.conftest import _State

TEMPLATE = "greeting_day_summary.jinja"

DAILY_FORECAST = [
    {
        "condition": "cloudy",
        "datetime": "2026-03-27T11:00:00+00:00",
        "temperature": 8.8,
    }
]

# Hourly forecast covering both the rain window (09–10 h) and the evening
# cool-down (warm at 18 h, drops below 21 °C at 19 h).
HOURLY_FORECAST = [
    {"condition": "rainy",       "datetime": "2026-03-27T09:00:00+00:00", "precipitation": 1.5, "temperature": 12.0},
    {"condition": "rainy",       "datetime": "2026-03-27T10:00:00+00:00", "precipitation": 1.2, "temperature": 13.0},
    {"condition": "cloudy",      "datetime": "2026-03-27T14:00:00+00:00", "precipitation": 0,   "temperature": 18.0},
    {"condition": "cloudy",      "datetime": "2026-03-27T18:00:00+00:00", "precipitation": 0,   "temperature": 22.0},
    {"condition": "clear-night", "datetime": "2026-03-27T19:00:00+00:00", "precipitation": 0,   "temperature": 20.5},
    {"condition": "clear-night", "datetime": "2026-03-27T20:00:00+00:00", "precipitation": 0,   "temperature": 19.0},
]

EVENTS_ONE_TIMED = [
    {
        "start": "2026-03-27T10:30:00+01:00",
        "end": "2026-03-27T11:00:00+01:00",
        "summary": "Kinderarzt",
        "location": "Kinderarzt",
    }
]

# One battery sensor below the default 20 % threshold, labelled AA.
MOTION = _State(
    "sensor.motion_battery", "8",
    {"device_class": "battery", "friendly_name": "Bewegungsmelder"},
)

EXPECTED = (
    "Guten Morgen, es ist 5Uhr 55.\n"
    "Das Wetter ist aktuell bewölkt und es wird höchstens 8.8 Grad warm.\n"
    "Heute regnet es von 9 bis 11 Uhr\n"
    "Ab 19 Uhr bleibt es unter 21 Grad.\n"
    "Folgende Familientermine sind für heute noch geplant:\n"
    "Kinderarzt von 10 Uhr 30 bis 11 Uhr\n"
    "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%, AA)"
)


def test_greeting_day_summary(render):
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 5, 55, 0),
        variables={
            "daily_forecast": DAILY_FORECAST,
            "hourly_forecast": HOURLY_FORECAST,
            "events": EVENTS_ONE_TIMED,
        },
        state_objects=[MOTION],
        labels={"battery_aa": ["sensor.motion_battery"]},
    )
    assert result == EXPECTED
