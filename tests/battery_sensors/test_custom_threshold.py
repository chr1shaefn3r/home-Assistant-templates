"""Battery sensors group — sensor reported as low only when using a custom threshold."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

SENSORS = [
    _State("sensor.motion_battery", "35", {"device_class": "battery", "friendly_name": "Bewegungsmelder"}),
    _State("sensor.door_battery",   "80", {"device_class": "battery", "friendly_name": "Türsensor"}),
]


def test_sensor_fine_at_default_threshold(render):
    # 35% is above the default 20% threshold — no output
    result = render(TEMPLATE, state_objects=SENSORS)
    assert result == ""


def test_sensor_low_at_custom_threshold(render):
    # 35% is below a custom 50% threshold — reported
    result = render(TEMPLATE, state_objects=SENSORS, variables={"threshold": 50})
    assert result == "Folgende Geräte haben niedrigen Akkustand: Bewegungsmelder (35%)"
