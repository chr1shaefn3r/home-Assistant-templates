"""Rain group — two independent rain windows scenario."""

TEMPLATE = "rain/daily_rain_summary.jinja"

# Group 1: 10:00–11:00 (rainy), gap at 12:00–13:00, Group 2: 14:00–15:00 (rainy)
FORECAST_TWO_GROUPS = [
    {"condition": "sunny",        "datetime": "2026-03-27T05:00:00+00:00", "wind_bearing": 337.8, "cloud_coverage":  1.6, "uv_index": 0.0, "temperature": -0.1, "wind_speed": 6.8, "precipitation": 0.0, "humidity": 92},
    {"condition": "sunny",        "datetime": "2026-03-27T06:00:00+00:00", "wind_bearing": 338.1, "cloud_coverage":  0.0, "uv_index": 0.1, "temperature":  0.2, "wind_speed": 7.6, "precipitation": 0.0, "humidity": 93},
    {"condition": "sunny",        "datetime": "2026-03-27T07:00:00+00:00", "wind_bearing": 339.8, "cloud_coverage":  0.0, "uv_index": 0.5, "temperature":  1.6, "wind_speed": 6.5, "precipitation": 0.0, "humidity": 88},
    {"condition": "partlycloudy", "datetime": "2026-03-27T08:00:00+00:00", "wind_bearing": 347.4, "cloud_coverage": 52.3, "uv_index": 1.1, "temperature":  3.2, "wind_speed": 8.3, "precipitation": 0.0, "humidity": 77},
    {"condition": "cloudy",       "datetime": "2026-03-27T09:00:00+00:00", "wind_bearing": 348.9, "cloud_coverage": 96.1, "uv_index": 2.0, "temperature":  4.5, "wind_speed": 7.6, "precipitation": 0.0, "humidity": 70},
    {"condition": "rainy",        "datetime": "2026-03-27T10:00:00+00:00", "wind_bearing": 344.3, "cloud_coverage": 94.5, "uv_index": 2.7, "temperature":  5.3, "wind_speed": 5.8, "precipitation": 2.3, "humidity": 85},
    {"condition": "rainy",        "datetime": "2026-03-27T11:00:00+00:00", "wind_bearing": 328.1, "cloud_coverage": 96.1, "uv_index": 3.2, "temperature":  6.1, "wind_speed": 6.1, "precipitation": 1.8, "humidity": 88},
    {"condition": "cloudy",       "datetime": "2026-03-27T12:00:00+00:00", "wind_bearing": 318.6, "cloud_coverage": 89.1, "uv_index": 3.2, "temperature":  6.9, "wind_speed": 6.5, "precipitation": 0.0, "humidity": 57},
    {"condition": "cloudy",       "datetime": "2026-03-27T13:00:00+00:00", "wind_bearing": 311.8, "cloud_coverage": 90.6, "uv_index": 2.6, "temperature":  7.4, "wind_speed": 6.1, "precipitation": 0.0, "humidity": 54},
    {"condition": "rainy",        "datetime": "2026-03-27T14:00:00+00:00", "wind_bearing": 306.8, "cloud_coverage":100.0, "uv_index": 1.9, "temperature":  7.6, "wind_speed": 6.8, "precipitation": 3.1, "humidity": 90},
    {"condition": "rainy",        "datetime": "2026-03-27T15:00:00+00:00", "wind_bearing": 302.5, "cloud_coverage": 82.8, "uv_index": 1.0, "temperature":  7.5, "wind_speed": 7.6, "precipitation": 1.2, "humidity": 87},
    {"condition": "partlycloudy", "datetime": "2026-03-27T16:00:00+00:00", "wind_bearing": 303.4, "cloud_coverage": 76.6, "uv_index": 0.4, "temperature":  7.5, "wind_speed": 7.6, "precipitation": 0.0, "humidity": 52},
    {"condition": "partlycloudy", "datetime": "2026-03-27T17:00:00+00:00", "wind_bearing": 283.6, "cloud_coverage": 49.2, "uv_index": 0.1, "temperature":  7.0, "wind_speed": 6.8, "precipitation": 0.0, "humidity": 58},
    {"condition": "clear-night",  "datetime": "2026-03-27T18:00:00+00:00", "wind_bearing": 217.3, "cloud_coverage":  3.1, "uv_index": 0.0, "temperature":  5.6, "wind_speed": 4.0, "precipitation": 0.0, "humidity": 67},
    {"condition": "clear-night",  "datetime": "2026-03-27T19:00:00+00:00", "wind_bearing": 120.5, "cloud_coverage":  2.3, "uv_index": 0.0, "temperature":  4.7, "wind_speed": 4.7, "precipitation": 0.0, "humidity": 67},
    {"condition": "clear-night",  "datetime": "2026-03-27T20:00:00+00:00", "wind_bearing": 121.1, "cloud_coverage":  1.6, "uv_index": 0.0, "temperature":  3.6, "wind_speed": 4.3, "precipitation": 0.0, "humidity": 71},
    {"condition": "clear-night",  "datetime": "2026-03-27T21:00:00+00:00", "wind_bearing": 158.2, "cloud_coverage":  1.6, "uv_index": 0.0, "temperature":  2.6, "wind_speed": 5.4, "precipitation": 0.0, "humidity": 75},
    {"condition": "clear-night",  "datetime": "2026-03-27T22:00:00+00:00", "wind_bearing": 182.7, "cloud_coverage":  3.1, "uv_index": 0.0, "temperature":  1.9, "wind_speed": 6.8, "precipitation": 0.0, "humidity": 78},
    {"condition": "clear-night",  "datetime": "2026-03-27T23:00:00+00:00", "wind_bearing": 159.4, "cloud_coverage":  0.0, "uv_index": 0.0, "temperature":  1.4, "wind_speed": 8.3, "precipitation": 0.0, "humidity": 80},
]


def test_two_rain_groups_message(render):
    result = render(TEMPLATE, variables={"forecast": FORECAST_TWO_GROUPS})
    assert "Heute regnet es von 10 bis 12 Uhr und von 14 bis 16 Uhr" in result
