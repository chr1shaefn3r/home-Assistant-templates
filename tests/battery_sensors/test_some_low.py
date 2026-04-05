"""Battery sensors group — one sensor below the default 20% threshold."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

SENSORS_ONE_LOW = [
    _State("sensor.motion_battery", "15", {"device_class": "battery", "friendly_name": "Bewegungsmelder"}),
    _State("sensor.door_battery",   "85", {"device_class": "battery", "friendly_name": "Türsensor"}),
]


def test_one_low_battery_reported(render):
    result = render(TEMPLATE, state_objects=SENSORS_ONE_LOW)
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (15%)"
