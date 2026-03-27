"""Greeting group — evening scenario (18:00 and later)."""
from datetime import datetime

TEMPLATE = "greeting/greeting.jinja"


def test_evening_greeting(render):
    result = render(TEMPLATE, now=datetime(2026, 3, 27, 20, 30, 0))
    assert "Guten Abend, es ist 20Uhr 30." in result
