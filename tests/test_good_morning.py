"""Tests for templates/automations/good_morning.jinja"""
import pytest

TEMPLATE = "automations/good_morning.jinja"


def test_greeting_with_known_name(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "18",
            "weather.forecast_home": "sunny",
        },
        attributes={"person.resident": {"friendly_name": "Alice"}},
    )
    assert "Good morning, Alice!" in result
    assert "18°C outside" in result
    assert "Enjoy the sunshine today!" in result


def test_greeting_without_name_falls_back(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "18",
            "weather.forecast_home": "cloudy",
        },
    )
    assert result.startswith("Good morning!")
    assert ", " not in result.splitlines()[0]


def test_cold_weather_warning(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "2",
            "weather.forecast_home": "snowy",
        },
    )
    assert "dress warmly" in result
    assert "Snow is expected today!" in result


def test_hot_weather_message(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "32",
            "weather.forecast_home": "sunny",
        },
        attributes={"person.resident": {"friendly_name": "Bob"}},
    )
    assert "Good morning, Bob!" in result
    assert "hot one" in result
    assert "Enjoy the sunshine today!" in result


def test_rainy_umbrella_reminder(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "14",
            "weather.forecast_home": "rainy",
        },
    )
    assert "umbrella" in result


def test_unavailable_sensor_uses_default(render):
    """When the temperature sensor is unavailable, the float filter must
    fall back to 0 — which triggers the 'dress warmly' cold-weather branch."""
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "unavailable",
            "weather.forecast_home": "cloudy",
        },
    )
    assert "0°C outside" in result
    assert "dress warmly" in result


def test_unknown_weather_shows_no_weather_line(render):
    result = render(
        TEMPLATE,
        states={
            "sensor.outdoor_temperature": "15",
            "weather.forecast_home": "cloudy",
        },
    )
    # None of the specific weather phrases should appear
    assert "sunshine" not in result
    assert "umbrella" not in result
    assert "Snow" not in result
