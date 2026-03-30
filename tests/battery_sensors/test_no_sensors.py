"""Battery sensors group — no battery sensors registered in HA."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"


def test_no_battery_sensors(render):
    result = render(TEMPLATE, state_objects=[])
    assert result == "Keine batteriebetriebenen Sensoren gefunden."
