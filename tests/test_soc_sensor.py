"Tests the state of charge sensor!"

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))


from unittest.mock import Mock

from e3dc_rscp_connect.entities import StateOfChargeSensor
import pytest


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


@pytest.fixture
def mock_storage():
    storage = Mock()
    storage.serial = "S10-123456789012"
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
    assert sensor._attr_unique_id == "s10_123456789012_soc"


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
