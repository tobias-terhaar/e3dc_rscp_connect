"""Tests for the per-wallbox energy sensor used by the energy dashboard."""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy

from e3dc_rscp_connect.e3dc_rscp_api import WallboxDataModel
from e3dc_rscp_connect.entities import WallboxEnergySensor, WallboxPowerSensor


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator(device_name="Test Wallbox", index=0):
    wallbox = WallboxDataModel(index=index)
    wallbox.device_name = device_name

    coordinator = Mock()
    coordinator.data = {}
    coordinator.storage.serial = "S10-2023-001"
    coordinator.get_wallbox.return_value = wallbox
    return coordinator


@pytest.fixture
def wallbox_power():
    """Mutable power value the sensor reads through its data getter."""
    return {"value": 0}


@pytest.fixture
def sensor(mock_entry, wallbox_power):
    return WallboxEnergySensor(
        _coordinator(),
        mock_entry,
        "Charged energy",
        0,
        lambda: wallbox_power["value"],
    )


def test_is_accepted_by_the_energy_dashboard(sensor):
    """kWh + energy + total_increasing is what the dashboard filters for."""
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR
    assert sensor.device_class == SensorDeviceClass.ENERGY
    assert sensor.state_class == SensorStateClass.TOTAL_INCREASING


def test_name_and_unique_id(sensor):
    assert sensor.name == "Charged energy"
    assert sensor.unique_id == "s10_2023_001_test_wallbox_0_charged_energy_energy"


def test_belongs_to_the_wallbox_device(sensor):
    assert "Wallbox" in sensor.device_info["name"]


def test_unique_id_differs_per_wallbox(mock_entry):
    ids = {
        WallboxEnergySensor(
            _coordinator(f"Wallbox {index}", index),
            mock_entry,
            "Charged energy",
            index,
            lambda: 0,
        ).unique_id
        for index in (0, 1)
    }

    assert len(ids) == 2


def test_counts_up_while_charging(sensor, wallbox_power):
    """Two updates an hour apart at 11 kW must add up to 11 kWh."""
    now = datetime.now(UTC)

    wallbox_power["value"] = 11000
    sensor._last_update = now - timedelta(hours=1)
    sensor._last_power = 11000
    sensor.hass = Mock()
    sensor.entity_id = "sensor.test"
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    assert sensor.native_value == pytest.approx(11.0, abs=0.01)


def test_power_sensor_has_a_state_class(mock_entry):
    """Without a state class the power value gets no statistics at all."""
    power_sensor = WallboxPowerSensor(
        _coordinator(), mock_entry, "Current power", 0, lambda: 0
    )

    assert power_sensor.state_class == SensorStateClass.MEASUREMENT
