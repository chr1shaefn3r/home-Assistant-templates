"""Rain group — no rain today, but rain tomorrow scenario."""
from datetime import datetime

TEMPLATE = "weather/daily_rain_summary.jinja"

FORECAST_NO_RAIN_TODAY_RAIN_TOMORROW = [
    # Today (2026-03-27) — no precipitation
    {"condition": "sunny",       "datetime": "2026-03-27T05:00:00+00:00", "precipitation": 0,   "temperature": -0.1},
    {"condition": "sunny",       "datetime": "2026-03-27T06:00:00+00:00", "precipitation": 0,   "temperature":  0.2},
    {"condition": "cloudy",      "datetime": "2026-03-27T10:00:00+00:00", "precipitation": 0,   "temperature":  5.3},
    {"condition": "partlycloudy","datetime": "2026-03-27T15:00:00+00:00", "precipitation": 0,   "temperature":  7.5},
    {"condition": "clear-night", "datetime": "2026-03-27T21:00:00+00:00", "precipitation": 0,   "temperature":  2.6},
    # Tomorrow (2026-03-28) — rain
    {"condition": "rainy",       "datetime": "2026-03-28T08:00:00+00:00", "precipitation": 1.2, "temperature":  6.0},
    {"condition": "rainy",       "datetime": "2026-03-28T09:00:00+00:00", "precipitation": 0.8, "temperature":  6.5},
    {"condition": "rainy",       "datetime": "2026-03-28T10:00:00+00:00", "precipitation": 1.5, "temperature":  7.0},
]


def test_no_rain_today_rain_tomorrow(render):
    result = render(
        TEMPLATE,
        now=datetime(2026, 3, 27, 5, 0, 0),
        variables={"forecast": FORECAST_NO_RAIN_TODAY_RAIN_TOMORROW},
    )
    assert result == "Heute bleibt es trocken"
