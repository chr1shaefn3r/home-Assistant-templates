"""Battery sensors group — multiple sensors below the default 20% threshold."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

SENSORS_MULTIPLE_LOW = [
    _State("sensor.motion_battery", "15", {"device_class": "battery", "friendly_name": "Bewegungsmelder"}),
    _State("sensor.door_battery",   "8",  {"device_class": "battery", "friendly_name": "Türsensor"}),
    _State("sensor.window_battery", "60", {"device_class": "battery", "friendly_name": "Fenstersensor"}),
]


def test_multiple_low_batteries_reported(render):
    result = render(TEMPLATE, state_objects=SENSORS_MULTIPLE_LOW)
    assert result == "Folgende Geräte haben niedrigen Akkustand: Bewegungsmelder (15%), Türsensor (8%)"
