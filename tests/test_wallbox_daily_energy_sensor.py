"""Tests for the per-wallbox daily energy sensor."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.util import dt as dt_util

from e3dc_rscp_connect.e3dc_rscp_api import WallboxDataModel
from e3dc_rscp_connect.entities import WallboxDailyEnergySensor

BERLIN = ZoneInfo("Europe/Berlin")
MODULE = "e3dc_rscp_connect.entities.wallbox_daily_energy_sensor.dt_util"


@pytest.fixture(autouse=True)
def berlin_timezone():
    """Run every test as if Home Assistant was configured for Europe/Berlin."""
    original = dt_util.get_default_time_zone()
    dt_util.set_default_time_zone(BERLIN)
    yield
    dt_util.set_default_time_zone(original)


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
def power():
    return {"value": 0}


@pytest.fixture
def sensor(mock_entry, power):
    sensor = WallboxDailyEnergySensor(
        _coordinator(),
        mock_entry,
        "Daily charged energy",
        0,
        lambda: power["value"],
    )
    sensor.hass = Mock()
    sensor.entity_id = "sensor.test"
    sensor.async_write_ha_state = Mock()
    return sensor


def test_is_disabled_by_default(sensor):
    assert sensor.entity_registry_enabled_default is False


def test_energy_dashboard_attributes(sensor):
    """A counter that restarts daily is a TOTAL with a last_reset."""
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.state_class == SensorStateClass.TOTAL


def test_name_and_unique_id(sensor):
    assert sensor.name == "Daily charged energy"
    assert (
        sensor.unique_id == "s10_2023_001_test_wallbox_0_daily_charged_energy_energy"
    )


def test_last_reset_is_local_midnight(sensor):
    last_reset = sensor.last_reset

    assert last_reset.tzinfo is not None
    assert last_reset.astimezone(BERLIN).hour == 0
    assert last_reset.astimezone(BERLIN).minute == 0


def test_counts_up_within_the_day(sensor, power):
    power["value"] = 11000
    sensor._last_update = datetime.now(UTC) - timedelta(hours=1)
    sensor._last_power = 11000

    sensor._handle_coordinator_update()

    assert sensor.native_value == pytest.approx(11.0, abs=0.01)


def test_resets_at_local_midnight(sensor, power):
    """A value from yesterday must not be carried into the new day."""
    midnight = dt_util.start_of_local_day()
    sensor._period_start = midnight - timedelta(days=1)
    sensor._energy_kwh = 42.0
    sensor._last_update = midnight - timedelta(minutes=30)
    sensor._last_power = 11000
    power["value"] = 11000

    with patch(f"{MODULE}.start_of_local_day", return_value=midnight):
        with patch(
            "e3dc_rscp_connect.entities.energy_sensor.datetime"
        ) as mocked_datetime:
            mocked_datetime.now.return_value = midnight + timedelta(minutes=30)
            sensor._handle_coordinator_update()

    # The 42 kWh of yesterday are gone, half an hour at 11 kW is left.
    assert sensor.native_value == pytest.approx(5.5, abs=0.01)
    assert sensor.last_reset == midnight


def test_energy_before_midnight_is_not_counted_twice(sensor, power):
    """The part of the interval before midnight belongs to the previous day."""
    midnight = dt_util.start_of_local_day()
    sensor._period_start = midnight - timedelta(days=1)
    sensor._energy_kwh = 5.0
    # last poll was well before midnight, the update happens right after it
    sensor._last_update = midnight - timedelta(hours=2)
    sensor._last_power = 10000
    power["value"] = 10000

    with patch(f"{MODULE}.start_of_local_day", return_value=midnight):
        with patch(
            "e3dc_rscp_connect.entities.energy_sensor.datetime"
        ) as mocked_datetime:
            mocked_datetime.now.return_value = midnight + timedelta(hours=1)
            sensor._handle_coordinator_update()

    # One hour at 10 kW after midnight, not three hours since the last poll.
    assert sensor.native_value == pytest.approx(10.0, abs=0.01)


def test_timezone_of_the_installation_is_used(mock_entry, power):
    """Midnight follows Home Assistant's time zone, not UTC."""
    dt_util.set_default_time_zone(ZoneInfo("Pacific/Auckland"))

    sensor = WallboxDailyEnergySensor(
        _coordinator(), mock_entry, "Daily charged energy", 0, lambda: 0
    )

    local_midnight = sensor.last_reset.astimezone(ZoneInfo("Pacific/Auckland"))
    assert local_midnight.hour == 0
    # Auckland is far enough from UTC that a UTC based day would differ.
    assert sensor.last_reset != sensor.last_reset.astimezone(UTC).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
