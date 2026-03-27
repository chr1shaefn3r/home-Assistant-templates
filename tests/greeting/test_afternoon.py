"""Greeting group — afternoon scenario (12:00–17:59)."""
from datetime import datetime

TEMPLATE = "greeting/greeting.jinja"


def test_afternoon_greeting(render):
    result = render(TEMPLATE, now=datetime(2026, 3, 27, 15, 5, 0))
    assert "Guten Nachmittag. es ist 15Uhr 5." in result
