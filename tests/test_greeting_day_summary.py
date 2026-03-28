"""Integration test — greeting_day_summary composes all four groups."""
from datetime import datetime

TEMPLATE = "greeting_day_summary.jinja"

DAILY_FORECAST = [
    {
        "condition": "cloudy",
        "datetime": "2026-03-27T11:00:00+00:00",
        "temperature": 8.8,
        "templow": 2.6,
        "wind_bearing": 322.9,
        "uv_index": 2.7,
        "wind_speed": 20.5,
        "precipitation": 0.8,
        "humidity": 56,
    }
]

HOURLY_FORECAST_NO_RAIN = [
    {"condition": "sunny",  "datetime": "2026-03-27T05:00:00+00:00", "precipitation": 0, "humidity": 92},
    {"condition": "sunny",  "datetime": "2026-03-27T06:00:00+00:00", "precipitation": 0, "humidity": 93},
    {"condition": "cloudy", "datetime": "2026-03-27T07:00:00+00:00", "precipitation": 0, "humidity": 88},
    {"condition": "cloudy", "datetime": "2026-03-27T08:00:00+00:00", "precipitation": 0, "humidity": 77},
    {"condition": "cloudy", "datetime": "2026-03-27T09:00:00+00:00", "precipitation": 0, "humidity": 70},
]

EVENTS_ONE_TIMED = [
    {
        "start": "2026-03-27T10:30:00+01:00",
        "end": "2026-03-27T11:00:00+01:00",
        "summary": "Kinderarzt",
        "location": "Kinderarzt",
    }
]

EXPECTED = (
    "Guten Morgen, es ist 5Uhr 55.\n"
    "Das Wetter ist aktuell bewölkt und es wird höchstens 8.8 Grad warm.\n"
    "Heute bleibt es trocken\n"
    "Folgende Familientermine sind für heute noch geplant:\n"
    "Kinderarzt von 10 Uhr 30 bis 11 Uhr"
)


def test_greeting_day_summary(render):
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 5, 55, 0),
        variables={
            "daily_forecast": DAILY_FORECAST,
            "hourly_forecast": HOURLY_FORECAST_NO_RAIN,
            "events": EVENTS_ONE_TIMED,
        },
    )
    assert result == EXPECTED
