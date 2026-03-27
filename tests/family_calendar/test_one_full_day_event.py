"""Calendar group — one full-day event scenario."""

TEMPLATE = "family_calendar/daily_family_summary.jinja"

EVENTS_ONE_FULL_DAY = [
    {
        "start": "2026-03-26",
        "end": "2026-03-27",
        "summary": "Osterfeier",
        "description": "Beispielbeschreibung",
        "location": "Kita",
    }
]


def test_one_full_day_event(render):
    result = render(TEMPLATE, variables={"events": EVENTS_ONE_FULL_DAY})
    assert "Folgende Familientermine sind für heute noch geplant:" in result
    assert "Osterfeier, Ganztagestermin" in result
