"""Tests for templates/sensors/time_of_day.jinja"""
from datetime import datetime

import pytest

TEMPLATE = "sensors/time_of_day.jinja"


@pytest.mark.parametrize(
    "hour, expected",
    [
        (0, "night"),
        (4, "night"),
        (5, "morning"),
        (8, "morning"),
        (11, "morning"),
        (12, "afternoon"),
        (14, "afternoon"),
        (16, "afternoon"),
        (17, "evening"),
        (20, "evening"),
        (21, "evening"),
        (22, "night"),
        (23, "night"),
    ],
)
def test_time_of_day_boundaries(render, hour, expected):
    result = render(TEMPLATE, now=datetime(2026, 1, 1, hour, 0, 0))
    assert result == expected
