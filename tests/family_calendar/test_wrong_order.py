"""Calendar group — two events returned in wrong order, template must sort them."""

TEMPLATE = "family_calendar/daily_family_summary.jinja"

# Later event (Elterngespräch 14:15) is returned first,
# earlier event (Zahnarzt 09:00) is returned second.
EVENTS_WRONG_ORDER = [
    {
        "start": "2026-03-27T14:15:00+01:00",
        "end": "2026-03-27T15:00:00+01:00",
        "summary": "Elterngespräch",
        "location": "Kita",
    },
    {
        "start": "2026-03-27T09:00:00+01:00",
        "end": "2026-03-27T09:30:00+01:00",
        "summary": "Zahnarzt",
        "location": "Zahnarztpraxis",
    },
]


def test_events_rendered_in_chronological_order(render):
    result = render(TEMPLATE, variables={"events": EVENTS_WRONG_ORDER})
    assert "Zahnarzt" in result
    assert "Elterngespräch" in result
    assert result.index("Zahnarzt") < result.index("Elterngespräch")
