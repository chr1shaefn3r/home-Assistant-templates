"""Battery sensors group — all sensors above the default threshold."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

SENSORS_ALL_FINE = [
    _State("sensor.motion_battery", "85", {"device_class": "battery", "friendly_name": "Bewegungsmelder"}),
    _State("sensor.door_battery",   "72", {"device_class": "battery", "friendly_name": "Türsensor"}),
    _State("sensor.window_battery", "21", {"device_class": "battery", "friendly_name": "Fenstersensor"}),
]


def test_all_fine_renders_empty(render):
    result = render(TEMPLATE, state_objects=SENSORS_ALL_FINE)
    assert result == ""
