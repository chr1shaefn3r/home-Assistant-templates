"""Battery sensors group — battery type shown when entity carries a battery_* label."""
from tests.conftest import _State

TEMPLATE = "battery_sensors/low_battery_summary.jinja"

MOTION = _State("sensor.motion_battery", "8",  {"device_class": "battery", "friendly_name": "Bewegungsmelder"})
DOOR   = _State("sensor.door_battery",   "12", {"device_class": "battery", "friendly_name": "Türsensor"})
PHONE  = _State("sensor.phone_battery",  "10", {"device_class": "battery", "friendly_name": "Handy"})


def test_single_sensor_with_type_label(render):
    result = render(TEMPLATE, state_objects=[MOTION],
                    labels={"battery_cr2032": ["sensor.motion_battery"]})
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%, CR2032)"


def test_single_sensor_without_type_label(render):
    result = render(TEMPLATE, state_objects=[MOTION])
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%)"


def test_multiple_sensors_different_types(render):
    result = render(TEMPLATE, state_objects=[MOTION, DOOR],
                    labels={
                        "battery_aa":     ["sensor.motion_battery"],
                        "battery_cr2032": ["sensor.door_battery"],
                    })
    assert result == "Folgende Geräte haben niedrigen Akkustand: Bewegungsmelder (8%, AA), Türsensor (12%, CR2032)"


def test_multiple_sensors_mixed_labelled(render):
    result = render(TEMPLATE, state_objects=[MOTION, DOOR],
                    labels={"battery_aa": ["sensor.motion_battery"]})
    assert result == "Folgende Geräte haben niedrigen Akkustand: Bewegungsmelder (8%, AA), Türsensor (12%)"


def test_rechargeable_excluded_type_label_ignored(render):
    result = render(TEMPLATE, state_objects=[PHONE, MOTION],
                    labels={
                        "rechargeable":   ["sensor.phone_battery"],
                        "battery_aa":     ["sensor.phone_battery"],
                        "battery_cr2032": ["sensor.motion_battery"],
                    })
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%, CR2032)"


def test_sensor_above_threshold_type_label_irrelevant(render):
    high = _State("sensor.motion_battery", "85", {"device_class": "battery", "friendly_name": "Bewegungsmelder"})
    result = render(TEMPLATE, state_objects=[high],
                    labels={"battery_aa": ["sensor.motion_battery"]})
    assert result == ""


def test_multi_battery_label(render):
    result = render(TEMPLATE, state_objects=[MOTION],
                    labels={"battery_aaa_2": ["sensor.motion_battery"]})
    assert result == "Folgendes Gerät hat einen niedrigen Akkustand: Bewegungsmelder (8%, 2x AAA)"
