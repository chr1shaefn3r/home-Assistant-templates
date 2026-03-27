"""Calendar group — two timed events on the same day, earlier one first."""

TEMPLATE = "family_calendar/daily_family_summary.jinja"

EVENTS_TWO_TIMED = [
    {
        "start": "2026-03-27T09:00:00+01:00",
        "end": "2026-03-27T09:30:00+01:00",
        "summary": "Zahnarzt",
        "location": "Zahnarztpraxis",
    },
    {
        "start": "2026-03-27T14:15:00+01:00",
        "end": "2026-03-27T15:00:00+01:00",
        "summary": "Elterngespräch",
        "location": "Kita",
    },
]


def test_two_timed_events_rendered_in_order(render):
    result = render(TEMPLATE, variables={"events": EVENTS_TWO_TIMED})
    assert "Folgende Familientermine sind für heute noch geplant:" in result
    # each event renders correctly
    assert "Zahnarzt von 9 Uhr bis 9 Uhr 30" in result
    assert "Elterngespräch von 14 Uhr 15 bis 15 Uhr" in result
    # earlier event appears before later event, separated by a newline
    assert "Zahnarzt von 9 Uhr bis 9 Uhr 30\nElterngespräch von 14 Uhr 15 bis 15 Uhr" in result
