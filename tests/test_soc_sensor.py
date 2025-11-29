"Tests the state of charge sensor!"

from unittest.mock import Mock

from config.custom_components.e3dc_rscp_connect.entities import StateOfChargeSensor
import pytest


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


@pytest.fixture
def mock_storage():
    storage = Mock()
    return storage


def test_state_of_charge_sensor_value(mock_entry, mock_storage) -> None:
    """Test that StateOfChargeSensor returns correct state of charge."""
    # Arrange
    coordinator = Mock()
    mock_storage.bat_soc = 85
    coordinator.storage = mock_storage

    sensor = StateOfChargeSensor(coordinator, mock_entry)

    # Act
    value = sensor.native_value

    # Assert
    assert value == 85
    assert sensor._attr_name == "Ladezustand"
    assert sensor._attr_native_unit_of_measurement == "%"
    assert sensor._attr_device_class.value == "battery"
    assert sensor._attr_unique_id == "e3dc_rscp_connect_ladezustand"


def test_power_sensor_missing_value(mock_entry, mock_storage) -> None:
    """Test StateOfChargeSensor when value is missing in coordinator data."""
    coordinator = Mock()
    coordinator.storage = mock_storage
    coordinator.storage.bat_soc = None

    sensor = StateOfChargeSensor(coordinator, mock_entry)

    # Act
    value = sensor.native_value

    # Assert
    assert value is None
