"""Tests for the Sun Mode sensor."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.entities.sun_mode_sensor import SunModeSensor


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {}
    coordinator.set_sun_mode = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def mock_wallbox_ident():
    """Create a mock wallbox identification data."""
    ident = Mock()
    ident.device_name = "Test Wallbox"
    return ident


@pytest.fixture
def mock_wallbox_data():
    """Create a mock wallbox data model."""
    wallbox = Mock()
    wallbox.sun_mode = None
    return wallbox


@pytest.fixture
def sun_mode_sensor(mock_coordinator, mock_entry, mock_wallbox_ident):
    """Create a SunModeSensor instance."""
    return SunModeSensor(mock_coordinator, mock_entry, 0, mock_wallbox_ident)


class TestSunModeSensor:
    """Test the SunModeSensor class."""

    def test_initialization(
        self, sun_mode_sensor, mock_coordinator, mock_entry, mock_wallbox_ident
    ):
        """Test sensor initialization."""
        assert sun_mode_sensor._attr_name == "Lademodus"
        assert sun_mode_sensor._attr_unique_id == "test_wallbox_sun_mode_state1"
        assert sun_mode_sensor.coordinator == mock_coordinator
        assert sun_mode_sensor._entry == mock_entry
        assert sun_mode_sensor._sub_device_index == 0
        assert sun_mode_sensor._attr_options == ["Sonnenmodus", "Mischmodus"]

    def test_initialization_with_different_wallbox_id(
        self, mock_coordinator, mock_entry, mock_wallbox_ident
    ):
        """Test sensor initialization with different wallbox ID."""
        sensor = SunModeSensor(mock_coordinator, mock_entry, 3, mock_wallbox_ident)
        assert sensor._sub_device_index == 3

    def test_initialization_device_name_formatting(self, mock_coordinator, mock_entry):
        """Test that device name is properly formatted in unique_id."""
        ident = Mock()
        ident.device_name = "My Cool Wallbox"
        sensor = SunModeSensor(mock_coordinator, mock_entry, 0, ident)
        assert sensor._attr_unique_id == "my_cool_wallbox_sun_mode_state1"

    def test_current_option_sun_mode_enabled(
        self, sun_mode_sensor, mock_coordinator, mock_wallbox_data
    ):
        """Test current_option returns 'Sonnenmodus' when sun_mode is True."""
        mock_wallbox_data.sun_mode = True
        mock_coordinator.data = {"wallbox_0": mock_wallbox_data}

        assert sun_mode_sensor.current_option == "Sonnenmodus"

    def test_current_option_sun_mode_disabled(
        self, sun_mode_sensor, mock_coordinator, mock_wallbox_data
    ):
        """Test current_option returns 'Mischmodus' when sun_mode is False."""
        mock_wallbox_data.sun_mode = False
        mock_coordinator.data = {"wallbox_0": mock_wallbox_data}

        assert sun_mode_sensor.current_option == "Mischmodus"

    def test_current_option_sun_mode_none(
        self, sun_mode_sensor, mock_coordinator, mock_wallbox_data
    ):
        """Test current_option returns None when sun_mode is None."""
        mock_wallbox_data.sun_mode = None
        mock_coordinator.data = {"wallbox_0": mock_wallbox_data}

        assert sun_mode_sensor.current_option is None

    def test_current_option_with_different_wallbox_id(
        self, mock_coordinator, mock_entry, mock_wallbox_ident, mock_wallbox_data
    ):
        """Test current_option retrieves correct wallbox data by ID."""
        sensor = SunModeSensor(mock_coordinator, mock_entry, 2, mock_wallbox_ident)
        mock_wallbox_data.sun_mode = True
        mock_coordinator.data = {"wallbox_2": mock_wallbox_data}

        assert sensor.current_option == "Sonnenmodus"

    @pytest.mark.asyncio
    async def test_async_select_option_sonnenmodus(
        self, sun_mode_sensor, mock_coordinator
    ):
        """Test selecting 'Sonnenmodus' option."""
        await sun_mode_sensor.async_select_option("Sonnenmodus")

        mock_coordinator.set_sun_mode.assert_called_once_with(0, True)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_select_option_mischmodus(
        self, sun_mode_sensor, mock_coordinator
    ):
        """Test selecting 'Mischmodus' option."""
        await sun_mode_sensor.async_select_option("Mischmodus")

        mock_coordinator.set_sun_mode.assert_called_once_with(0, False)
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_select_option_with_different_wallbox_id(
        self, mock_coordinator, mock_entry, mock_wallbox_ident
    ):
        """Test that correct wallbox ID is used when setting sun mode."""
        sensor = SunModeSensor(mock_coordinator, mock_entry, 5, mock_wallbox_ident)
        await sensor.async_select_option("Sonnenmodus")

        mock_coordinator.set_sun_mode.assert_called_once_with(5, True)

    @pytest.mark.asyncio
    async def test_async_select_option_invalid_option(
        self, sun_mode_sensor, mock_coordinator
    ):
        """Test that invalid option does not call set_sun_mode."""
        await sun_mode_sensor.async_select_option("InvalidMode")

        mock_coordinator.set_sun_mode.assert_not_called()
        # Refresh should still be called
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_is_select_entity(self, sun_mode_sensor):
        """Test that SunModeSensor is a SelectEntity."""
        from homeassistant.components.select import SelectEntity

        assert isinstance(sun_mode_sensor, SelectEntity)

    def test_inherits_from_e3dc_connect_entity(self, sun_mode_sensor):
        """Test that SunModeSensor inherits from E3dcConnectEntity."""
        from e3dc_rscp_connect.entities.entity import E3dcConnectEntity

        assert isinstance(sun_mode_sensor, E3dcConnectEntity)

    def test_options_are_immutable(self, sun_mode_sensor):
        """Test that available options are correctly set."""
        assert sun_mode_sensor._options == ["Sonnenmodus", "Mischmodus"]
        assert sun_mode_sensor._attr_options == ["Sonnenmodus", "Mischmodus"]
