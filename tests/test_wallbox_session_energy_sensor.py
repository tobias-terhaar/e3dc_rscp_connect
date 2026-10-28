"""Tests for the per-wallbox charging session energy sensor."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy

from e3dc_rscp_connect.e3dc_rscp_api import WallboxDataModel
from e3dc_rscp_connect.entities import WallboxSessionEnergySensor
from e3dc_rscp_connect.entities.wallbox_session_energy_sensor import is_car_connected


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator():
    wallbox = WallboxDataModel(index=0)
    wallbox.device_name = "Test Wallbox"

    coordinator = Mock()
    coordinator.data = {}
    coordinator.storage.serial = "S10-2023-001"
    coordinator.get_wallbox.return_value = wallbox
    return coordinator


@pytest.fixture
def wallbox():
    """The values the sensor reads, mutated by the tests."""
    return {"power": 0, "cp_state": "A"}


@pytest.fixture
def sensor(mock_entry, wallbox):
    sensor = WallboxSessionEnergySensor(
        _coordinator(),
        mock_entry,
        "session_charged_energy",
        0,
        lambda: wallbox["power"],
        lambda: wallbox["cp_state"],
    )
    sensor.hass = Mock()
    sensor.entity_id = "sensor.test"
    sensor.async_write_ha_state = Mock()
    return sensor


def _update(sensor, at):
    """Runs one coordinator update at the given point in time."""
    with patch("e3dc_rscp_connect.entities.energy_sensor.datetime") as mocked:
        mocked.now.return_value = at
        sensor._handle_coordinator_update()


# --- CP state mapping ------------------------------------------------------


@pytest.mark.parametrize("state", ["A", "A1", "a"])
def test_a_states_mean_no_car(state):
    assert is_car_connected(state) is False


@pytest.mark.parametrize("state", ["B", "B1", "B2", "C", "C1", "C2"])
def test_b_and_c_states_mean_car_connected(state):
    assert is_car_connected(state) is True


@pytest.mark.parametrize("state", ["F", None, "", "X"])
def test_other_states_say_nothing(state):
    assert is_car_connected(state) is None


# --- Entity attributes -----------------------------------------------------


def test_is_disabled_by_default(sensor):
    assert sensor.entity_registry_enabled_default is False


def test_energy_attributes(sensor):
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.state_class == SensorStateClass.TOTAL


def test_name_and_unique_id(sensor):
    assert sensor.translation_key == "session_charged_energy"
    assert (
        sensor.unique_id
        == "s10_2023_001_test_wallbox_0_session_charged_energy_energy"
    )


# --- Session handling ------------------------------------------------------


def test_no_counting_while_no_car_is_connected(sensor, wallbox):
    start = datetime.now(UTC)
    wallbox["cp_state"] = "A"
    wallbox["power"] = 11000  # would be odd, but must not be counted

    _update(sensor, start)
    _update(sensor, start + timedelta(hours=1))

    assert sensor.native_value == 0.0
    assert sensor.last_reset is None


def test_session_counts_from_plugging_in(sensor, wallbox):
    start = datetime.now(UTC)

    wallbox["cp_state"] = "A"
    _update(sensor, start)

    # car plugged in, then charging for an hour at 11 kW
    wallbox["cp_state"] = "B"
    wallbox["power"] = 11000
    _update(sensor, start + timedelta(minutes=1))

    wallbox["cp_state"] = "C"
    _update(sensor, start + timedelta(minutes=61))

    assert sensor.native_value == pytest.approx(11.0, abs=0.01)
    assert sensor.last_reset is not None


def test_session_starting_directly_with_charging(sensor, wallbox):
    """A to C without seeing B in between still starts a session."""
    start = datetime.now(UTC)
    wallbox["cp_state"] = "A"
    _update(sensor, start)

    wallbox["cp_state"] = "C"
    wallbox["power"] = 11000
    _update(sensor, start + timedelta(minutes=1))
    _update(sensor, start + timedelta(minutes=31))

    assert sensor.native_value == pytest.approx(5.5, abs=0.01)


def test_value_is_kept_after_the_car_left(sensor, wallbox):
    start = datetime.now(UTC)
    wallbox["cp_state"] = "A"
    _update(sensor, start)

    wallbox["cp_state"] = "C"
    wallbox["power"] = 11000
    _update(sensor, start + timedelta(minutes=1))
    _update(sensor, start + timedelta(minutes=61))

    # car unplugged
    wallbox["cp_state"] = "A"
    wallbox["power"] = 0
    _update(sensor, start + timedelta(minutes=62))

    value_at_end = sensor.native_value
    assert value_at_end == pytest.approx(11.0, abs=0.1)

    # hours later, still the value of that session
    _update(sensor, start + timedelta(hours=8))
    assert sensor.native_value == value_at_end


def test_next_session_starts_from_zero(sensor, wallbox):
    start = datetime.now(UTC)
    wallbox["cp_state"] = "A"
    _update(sensor, start)

    wallbox["cp_state"] = "C"
    wallbox["power"] = 11000
    _update(sensor, start + timedelta(minutes=1))
    _update(sensor, start + timedelta(minutes=61))

    wallbox["cp_state"] = "A"
    wallbox["power"] = 0
    _update(sensor, start + timedelta(minutes=62))
    first_session = sensor.native_value

    # a new car arrives much later
    wallbox["cp_state"] = "C"
    wallbox["power"] = 4000
    _update(sensor, start + timedelta(hours=8))
    _update(sensor, start + timedelta(hours=9))

    assert first_session == pytest.approx(11.0, abs=0.1)
    # only the new session, and the eight hours in between are not in it
    assert sensor.native_value == pytest.approx(4.0, abs=0.01)


def test_error_state_does_not_end_the_session(sensor, wallbox):
    start = datetime.now(UTC)
    wallbox["cp_state"] = "A"
    _update(sensor, start)

    wallbox["cp_state"] = "C"
    wallbox["power"] = 11000
    _update(sensor, start + timedelta(minutes=1))

    wallbox["cp_state"] = "F"
    _update(sensor, start + timedelta(minutes=61))

    assert sensor._session_active is True
    assert sensor.native_value == pytest.approx(11.0, abs=0.01)


def test_running_session_survives_a_restart(sensor, wallbox):
    """After a restart the first state seen is not a transition."""
    start = datetime.now(UTC)
    # as if restored from the recorder
    sensor._energy_kwh = 6.0
    wallbox["cp_state"] = "C"
    wallbox["power"] = 11000

    _update(sensor, start)
    _update(sensor, start + timedelta(hours=1))

    assert sensor._session_active is True
    assert sensor.native_value == pytest.approx(17.0, abs=0.01)
