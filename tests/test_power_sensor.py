from unittest.mock import Mock
import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfPower

from config.custom_components.e3dc_rscp_connect.entities import PowerSensor


class MockCoordinator:
    """Simple mock of the E3dcRscpCoordinator with .data."""

    def __init__(self, data=None, storage=None):
        self.data = data or {}
        self.storage = storage


@pytest.fixture
def mock_entry():
    """Return a mock config entry."""
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def test_power_sensor_attributes_sensor_value_id(mock_entry):
    """Test PowerSensor basic attributes and native_value."""
    mock_data = {"power_ac": 1234}
    coordinator = MockCoordinator(data=mock_data)

    sensor = PowerSensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="AC Power",
        sensor_value_id="power_ac",
    )

    assert sensor.name == "AC Power"
    assert sensor.unique_id == "e3dc_rscp_connect_power_ac_power"
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_value == 1234


def test_power_sensor_attributes_data_getter(mock_entry):
    """Test PowerSensor basic attributes and native_value."""

    storage = Mock()
    storage.powers.home = 75
    coordinator = MockCoordinator(storage=storage)

    sensor = PowerSensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="Home Power",
        data_getter=lambda: coordinator.storage.powers.home,
    )

    assert sensor.name == "Home Power"
    assert sensor.unique_id == "e3dc_rscp_connect_power_home_power"
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.device_class == SensorDeviceClass.POWER
    assert sensor.native_value == 75

    storage.powers.home = 80
    assert sensor.native_value == 80


def test_power_sensor_missing_value(mock_entry):
    """Test PowerSensor when value is missing in coordinator data."""
    coordinator = MockCoordinator(data={})
    sensor = PowerSensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="AC Power",
        sensor_value_id="power_ac",
    )

    assert sensor.native_value is None
