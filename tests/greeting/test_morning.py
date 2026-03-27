"""Greeting group — morning scenario (before 12:00)."""
from datetime import datetime

TEMPLATE = "greeting/greeting.jinja"


def test_morning_greeting(render):
    result = render(TEMPLATE, now=datetime(2026, 3, 27, 5, 55, 0))
    assert "Guten Morgen, es ist 5Uhr 55." in result
