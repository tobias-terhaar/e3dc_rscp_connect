from unittest.mock import Mock
import pytest
from datetime import datetime, timedelta, UTC
from config.custom_components.e3dc_rscp_connect.entities import EnergySensor


class MockCoordinator:
    def __init__(self, data=None):
        self.data = data or {}
        self._listeners = []

    def async_add_listener(self, callback, context=None):
        self._listeners.append(callback)

    def update_value(self, key, value):
        self.data[key] = value
        for cb in self._listeners:
            cb()


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


@pytest.fixture
def coordinator():
    return MockCoordinator()


def test_energy_sensor_attributes(coordinator, mock_entry):
    """Test basic attributes of the energy sensor."""
    sensor = EnergySensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="Grid Import",
        power_value="grid_power",
    )

    assert sensor.name == "Grid Import"
    assert sensor.unique_id == "e3dc_rscp_connect_energy_grid_import"
    assert sensor.native_unit_of_measurement == "kWh"
    assert sensor.device_class == "energy"
    assert sensor.state_class == "total_increasing"
    assert sensor.native_value == 0.0


@pytest.mark.asyncio
async def test_restore_last_state(coordinator, mock_entry):
    """Test restore of last known state."""
    sensor = EnergySensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="Grid Import",
        power_value="grid_power",
    )

    async def mock_get_last_state():
        return type("State", (), {"state": "12.345"})

    sensor.async_get_last_state = mock_get_last_state
    await sensor.async_added_to_hass()

    assert sensor.native_value == 12.345


@pytest.mark.asyncio
async def test_energy_calculation_positive_flow(coordinator, mock_entry):
    """Test energy accumulation in positive direction."""
    sensor = EnergySensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="Grid Import",
        power_value="grid_power",
    )

    sensor.hass = Mock()
    sensor.async_write_ha_state = Mock()

    now = datetime.now(UTC)
    sensor._last_update = now - timedelta(seconds=3600)
    sensor._last_power = 1000  # 1 kW

    coordinator.data["grid_power"] = 2000  # 2 kW
    sensor._handle_coordinator_update()

    # Durchschnittsleistung: (1000+2000)/2 = 1500 W = 1.5 kW
    # Dauer: 1 h → Energie: 1.5 kWh
    assert round(sensor.native_value, 3) == 1.5


@pytest.mark.asyncio
async def test_energy_calculation_negative_flow(coordinator, mock_entry):
    """Test energy accumulation in negative direction with reverse sign."""
    sensor = EnergySensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="Grid Export",
        power_value="grid_power",
        negative_direction=True,
    )
    sensor.hass = Mock()
    sensor.async_write_ha_state = Mock()

    # initialize sensor!
    coordinator.data["grid_power"] = -2000  # -2 kW (-> zählt als +2kW)
    sensor._handle_coordinator_update()

    now = datetime.now(UTC)
    sensor._last_update = now - timedelta(seconds=1800)  # 0.5 h

    coordinator.data["grid_power"] = -1000  # -1 kW (-> zählt als +1kW)
    sensor._handle_coordinator_update()

    # Durchschnitt: (2+1)/2 = 1.5 kW, Dauer: 0.5 h → Energie: 0.75 kWh
    assert round(sensor.native_value, 3) == 0.75


def test_missing_power_value_handling(coordinator, mock_entry):
    """Test no exception when power value is missing in coordinator data."""
    sensor = EnergySensor(
        coordinator=coordinator,
        entry=mock_entry,
        name="PV",
        power_value="pv_power",
    )

    # No data yet
    sensor._handle_coordinator_update()

    assert sensor.native_value == 0.0
