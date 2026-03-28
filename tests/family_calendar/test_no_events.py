"""Calendar group — no events scenario."""

TEMPLATE = "family_calendar/daily_family_summary.jinja"

EVENTS_EMPTY = []


def test_no_events(render):
    result = render(TEMPLATE, variables={"events": EVENTS_EMPTY})
    assert result == "Es sind keine Familientermine für den Rest des Tages geplant."
