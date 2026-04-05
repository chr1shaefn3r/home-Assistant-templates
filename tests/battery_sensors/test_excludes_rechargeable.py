"""Battery sensors group — rechargeable devices are excluded even when below threshold."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

SENSORS = [
    _State("sensor.phone_battery",  "12", {"device_class": "battery", "friendly_name": "Handy"}),
    _State("sensor.motion_battery", "8",  {"device_class": "battery", "friendly_name": "Bewegungsmelder"}),
]

LABELS = {"rechargeable": ["sensor.phone_battery"]}


def test_rechargeable_sensor_excluded(render):
    result = render(TEMPLATE, state_objects=SENSORS, labels=LABELS)
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%)"
