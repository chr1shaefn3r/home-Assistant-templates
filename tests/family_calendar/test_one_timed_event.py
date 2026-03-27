"""Calendar group — one timed appointment scenario."""

TEMPLATE = "family_calendar/daily_family_summary.jinja"

EVENTS_ONE_TIMED = [
    {
        "start": "2026-03-27T10:30:00+01:00",
        "end": "2026-03-27T11:00:00+01:00",
        "summary": "Kinderarzt",
        "location": "Kinderarzt",
    }
]


def test_one_timed_event(render):
    result = render(TEMPLATE, variables={"events": EVENTS_ONE_TIMED})
    assert "Folgende Familientermine sind für heute noch geplant:" in result
    assert "Kinderarzt von 10 Uhr 30 bis 11 Uhr" in result
