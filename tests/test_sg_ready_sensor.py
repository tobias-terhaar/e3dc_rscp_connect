"""Tests for the SG Ready sensor."""

from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.entities.sg_ready_sensor import SGReadySensor


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {}
    return coordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def sg_ready_sensor(mock_coordinator, mock_entry):
    """Create a SGReadySensor instance."""
    return SGReadySensor(mock_coordinator, mock_entry)


class TestSGReadySensor:
    """Test the SGReadySensor class."""

    def test_initialization(self, sg_ready_sensor, mock_coordinator, mock_entry):
        """Test sensor initialization."""
        assert sg_ready_sensor._attr_name == "SG Ready Status"
        assert sg_ready_sensor._attr_unique_id == "sg_ready_state"
        assert sg_ready_sensor.coordinator == mock_coordinator
        assert sg_ready_sensor._entry == mock_entry

    def test_native_value_block_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Block' for state 1."""
        mock_coordinator.data = {"sg_ready_state": 1}
        assert sg_ready_sensor.native_value == "Block"

    def test_native_value_normal_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Normal' for state 2."""
        mock_coordinator.data = {"sg_ready_state": 2}
        assert sg_ready_sensor.native_value == "Normal"

    def test_native_value_go_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Go' for state 3."""
        mock_coordinator.data = {"sg_ready_state": 3}
        assert sg_ready_sensor.native_value == "Go"

    def test_native_value_force_go_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Force Go' for state 4."""
        mock_coordinator.data = {"sg_ready_state": 4}
        assert sg_ready_sensor.native_value == "Force Go"

    def test_native_value_unknown_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Unknown' for invalid state."""
        mock_coordinator.data = {"sg_ready_state": 99}
        assert sg_ready_sensor.native_value == "Unknown"

    def test_native_value_missing_key(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Unknown' when key is missing."""
        mock_coordinator.data = {}
        assert sg_ready_sensor.native_value == "Unknown"

    def test_native_value_none_state(self, sg_ready_sensor, mock_coordinator):
        """Test native_value returns 'Unknown' when state is None."""
        mock_coordinator.data = {"sg_ready_state": None}
        assert sg_ready_sensor.native_value == "Unknown"

    def test_is_sensor_entity(self, sg_ready_sensor):
        """Test that SGReadySensor is a SensorEntity."""
        from homeassistant.components.sensor import SensorEntity

        assert isinstance(sg_ready_sensor, SensorEntity)

    def test_inherits_from_e3dc_connect_entity(self, sg_ready_sensor):
        """Test that SGReadySensor inherits from E3dcConnectEntity."""
        from e3dc_rscp_connect.entities.entity import E3dcConnectEntity

        assert isinstance(sg_ready_sensor, E3dcConnectEntity)
