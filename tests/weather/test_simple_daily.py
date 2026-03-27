"""Weather group — simple daily summary scenario."""

TEMPLATE = "weather/daily_weather_summary.jinja"

FORECAST_CLOUDY = [
    {
        "condition": "cloudy",
        "datetime": "2026-03-26T11:00:00+00:00",
        "wind_bearing": 322.9,
        "uv_index": 2.7,
        "temperature": 8.8,
        "templow": 2.6,
        "wind_speed": 20.5,
        "precipitation": 0.8,
        "humidity": 56,
    }
]


def test_cloudy_daily_summary(render):
    result = render(TEMPLATE, variables={"forecast": FORECAST_CLOUDY})
    assert "Das Wetter ist aktuell bewölkt und es wird höchstens 8.8 Grad warm." in result
