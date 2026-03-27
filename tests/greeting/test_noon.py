"""Greeting group — noon scenario (11:00–12:59)."""
from datetime import datetime

TEMPLATE = "greeting/greeting.jinja"


def test_noon_greeting(render):
    result = render(TEMPLATE, now=datetime(2026, 3, 27, 12, 15, 0))
    assert "Guten Mittag, es ist 12Uhr 15." in result
