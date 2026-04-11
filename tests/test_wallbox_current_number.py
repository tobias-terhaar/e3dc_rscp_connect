"""Tests for the wallbox current number entities."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.entities.wallbox_current_number import (
    WallboxMaxCurrentNumber,
    WallboxMinCurrentNumber,
)
from e3dc_rscp_connect.model.WallboxDataModel import WallboxCurrentModel, WallboxDataModel


# --- Fixtures ---


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


@pytest.fixture
def mock_coordinator():
    coordinator = Mock()
    coordinator.data = {}
    coordinator.storage.serial = "S10-2023-001"
    coordinator.set_max_charge_current = AsyncMock()
    coordinator.set_min_charge_current = AsyncMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_wallbox():
    wallbox = WallboxDataModel(index=0)
    wallbox.device_name = "Test Wallbox"
    wallbox.currents = WallboxCurrentModel(
        upper_limit=16,
        lower_limit=6,
        max=14,
        min=8,
    )
    return wallbox


@pytest.fixture
def max_entity(mock_coordinator, mock_entry, mock_wallbox):
    return WallboxMaxCurrentNumber(mock_coordinator, mock_entry, mock_wallbox)


@pytest.fixture
def min_entity(mock_coordinator, mock_entry, mock_wallbox):
    return WallboxMinCurrentNumber(mock_coordinator, mock_entry, mock_wallbox)


# --- WallboxMaxCurrentNumber ---


class TestWallboxMaxCurrentNumber:

    def test_initialization(self, max_entity, mock_coordinator, mock_entry):
        """Test that name, unique_id and wallbox index are set correctly."""
        assert max_entity._attr_name == "Max Ladestrom"
        assert max_entity._attr_unique_id == "s10_2023_001_test_wallbox_max_charge_current"
        assert max_entity._sub_device_index == 0

    def test_initialization_different_wallbox_index(self, mock_coordinator, mock_entry, mock_wallbox):
        """Test that the wallbox index is stored correctly."""
        mock_wallbox.index = 3
        entity = WallboxMaxCurrentNumber(mock_coordinator, mock_entry, mock_wallbox)
        assert entity._sub_device_index == 3

    def test_native_value_returns_real_max(self, max_entity, mock_coordinator, mock_wallbox):
        """native_value returns currents.max from the device when no assumed value is set."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert max_entity.native_value == 14.0

    def test_native_value_returns_assumed_value_when_set(self, max_entity, mock_coordinator, mock_wallbox):
        """native_value returns the optimistic value while waiting for device confirmation."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        max_entity._assumed_value = 10.0
        assert max_entity.native_value == 10.0

    def test_native_value_returns_none_without_wallbox(self, max_entity, mock_coordinator):
        """native_value returns None when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert max_entity.native_value is None

    def test_native_min_value(self, max_entity, mock_coordinator, mock_wallbox):
        """native_min_value equals lower_limit from the device."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert max_entity.native_min_value == 6.0

    def test_native_max_value(self, max_entity, mock_coordinator, mock_wallbox):
        """native_max_value equals upper_limit from the device."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert max_entity.native_max_value == 16.0

    def test_native_min_value_fallback_without_wallbox(self, max_entity, mock_coordinator):
        """native_min_value returns 0.0 when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert max_entity.native_min_value == 0.0

    def test_native_max_value_fallback_without_wallbox(self, max_entity, mock_coordinator):
        """native_max_value returns 32.0 when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert max_entity.native_max_value == 32.0

    def test_assumed_state_false_initially(self, max_entity):
        """assumed_state is False when no optimistic value is pending."""
        assert max_entity.assumed_state is False

    def test_assumed_state_true_when_value_pending(self, max_entity):
        """assumed_state is True while an optimistic value is pending."""
        max_entity._assumed_value = 12.0
        assert max_entity.assumed_state is True

    @pytest.mark.asyncio
    async def test_async_set_native_value_stores_assumed_value(self, max_entity, mock_coordinator):
        """Setting a value stores it as the assumed value."""
        with patch.object(max_entity, "async_write_ha_state"):
            await max_entity.async_set_native_value(12.0)
        assert max_entity._assumed_value == 12.0

    @pytest.mark.asyncio
    async def test_async_set_native_value_writes_ha_state_immediately(self, max_entity, mock_coordinator):
        """HA state is written immediately before the device call completes."""
        with patch.object(max_entity, "async_write_ha_state") as mock_write:
            await max_entity.async_set_native_value(12.0)
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_calls_coordinator(self, max_entity, mock_coordinator):
        """Setting a value sends the correct command to the coordinator."""
        with patch.object(max_entity, "async_write_ha_state"):
            await max_entity.async_set_native_value(12.0)
        mock_coordinator.set_max_charge_current.assert_called_once_with(0, 12)

    @pytest.mark.asyncio
    async def test_async_set_native_value_triggers_refresh(self, max_entity, mock_coordinator):
        """A coordinator refresh is triggered after the device call."""
        with patch.object(max_entity, "async_write_ha_state"):
            await max_entity.async_set_native_value(12.0)
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_handle_coordinator_update_clears_assumed_value(self, max_entity):
        """Coordinator update clears the pending optimistic value."""
        max_entity._assumed_value = 12.0
        with patch.object(max_entity, "async_write_ha_state"):
            max_entity._handle_coordinator_update()
        assert max_entity._assumed_value is None

    def test_optimistic_flow_accepted_by_device(self, max_entity, mock_coordinator, mock_wallbox):
        """Full optimistic flow: assumed value shown, then real device value after update."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox

        # Before set: real value
        assert max_entity.native_value == 14.0

        # After optimistic set: assumed value shown
        max_entity._assumed_value = 12.0
        assert max_entity.native_value == 12.0
        assert max_entity.assumed_state is True

        # Device confirmed: coordinator returns new value, assumed clears
        mock_wallbox.currents.max = 12
        with patch.object(max_entity, "async_write_ha_state"):
            max_entity._handle_coordinator_update()

        assert max_entity._assumed_value is None
        assert max_entity.native_value == 12.0

    def test_optimistic_flow_rejected_by_device(self, max_entity, mock_coordinator, mock_wallbox):
        """If the device rejects the change, the real value is shown after the update."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox

        # Optimistic set to 12, but device still has 14
        max_entity._assumed_value = 12.0
        assert max_entity.native_value == 12.0

        # Device did not accept: coordinator still returns 14
        with patch.object(max_entity, "async_write_ha_state"):
            max_entity._handle_coordinator_update()

        assert max_entity._assumed_value is None
        assert max_entity.native_value == 14.0  # reverted

    def test_is_number_entity(self, max_entity):
        from homeassistant.components.number import NumberEntity
        assert isinstance(max_entity, NumberEntity)

    def test_device_class(self, max_entity):
        from homeassistant.components.number import NumberDeviceClass
        assert max_entity._attr_device_class == NumberDeviceClass.CURRENT

    def test_unit_of_measurement(self, max_entity):
        from homeassistant.const import UnitOfElectricCurrent
        assert max_entity._attr_native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    def test_step(self, max_entity):
        assert max_entity._attr_native_step == 1


# --- WallboxMinCurrentNumber ---


class TestWallboxMinCurrentNumber:

    def test_initialization(self, min_entity, mock_coordinator, mock_entry):
        """Test that name, unique_id and wallbox index are set correctly."""
        assert min_entity._attr_name == "Min Ladestrom"
        assert min_entity._attr_unique_id == "s10_2023_001_test_wallbox_min_charge_current"
        assert min_entity._sub_device_index == 0

    def test_native_value_returns_real_min(self, min_entity, mock_coordinator, mock_wallbox):
        """native_value returns currents.min from the device when no assumed value is set."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert min_entity.native_value == 8.0

    def test_native_value_returns_assumed_value_when_set(self, min_entity, mock_coordinator, mock_wallbox):
        """native_value returns the optimistic value while waiting for device confirmation."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        min_entity._assumed_value = 10.0
        assert min_entity.native_value == 10.0

    def test_native_value_returns_none_without_wallbox(self, min_entity, mock_coordinator):
        """native_value returns None when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert min_entity.native_value is None

    def test_native_min_value(self, min_entity, mock_coordinator, mock_wallbox):
        """native_min_value equals lower_limit from the device."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert min_entity.native_min_value == 6.0

    def test_native_max_value_is_capped_at_max_current(self, min_entity, mock_coordinator, mock_wallbox):
        """native_max_value for min entity is capped at currents.max, not upper_limit."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        assert min_entity.native_max_value == 14.0  # currents.max, not upper_limit (16)

    def test_native_max_value_tracks_max_current_changes(self, min_entity, mock_coordinator, mock_wallbox):
        """native_max_value updates dynamically when currents.max changes."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox
        mock_wallbox.currents.max = 10
        assert min_entity.native_max_value == 10.0

    def test_native_min_value_fallback_without_wallbox(self, min_entity, mock_coordinator):
        """native_min_value returns 0.0 when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert min_entity.native_min_value == 0.0

    def test_native_max_value_fallback_without_wallbox(self, min_entity, mock_coordinator):
        """native_max_value returns 32.0 when the wallbox is not available."""
        mock_coordinator.get_wallbox.return_value = None
        assert min_entity.native_max_value == 32.0

    def test_assumed_state_false_initially(self, min_entity):
        """assumed_state is False when no optimistic value is pending."""
        assert min_entity.assumed_state is False

    def test_assumed_state_true_when_value_pending(self, min_entity):
        """assumed_state is True while an optimistic value is pending."""
        min_entity._assumed_value = 7.0
        assert min_entity.assumed_state is True

    @pytest.mark.asyncio
    async def test_async_set_native_value_stores_assumed_value(self, min_entity, mock_coordinator):
        """Setting a value stores it as the assumed value."""
        with patch.object(min_entity, "async_write_ha_state"):
            await min_entity.async_set_native_value(7.0)
        assert min_entity._assumed_value == 7.0

    @pytest.mark.asyncio
    async def test_async_set_native_value_writes_ha_state_immediately(self, min_entity, mock_coordinator):
        """HA state is written immediately before the device call completes."""
        with patch.object(min_entity, "async_write_ha_state") as mock_write:
            await min_entity.async_set_native_value(7.0)
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_native_value_calls_coordinator(self, min_entity, mock_coordinator):
        """Setting a value sends the correct command to the coordinator."""
        with patch.object(min_entity, "async_write_ha_state"):
            await min_entity.async_set_native_value(7.0)
        mock_coordinator.set_min_charge_current.assert_called_once_with(0, 7)

    @pytest.mark.asyncio
    async def test_async_set_native_value_triggers_refresh(self, min_entity, mock_coordinator):
        """A coordinator refresh is triggered after the device call."""
        with patch.object(min_entity, "async_write_ha_state"):
            await min_entity.async_set_native_value(7.0)
        mock_coordinator.async_request_refresh.assert_called_once()

    def test_handle_coordinator_update_clears_assumed_value(self, min_entity):
        """Coordinator update clears the pending optimistic value."""
        min_entity._assumed_value = 7.0
        with patch.object(min_entity, "async_write_ha_state"):
            min_entity._handle_coordinator_update()
        assert min_entity._assumed_value is None

    def test_optimistic_flow_accepted_by_device(self, min_entity, mock_coordinator, mock_wallbox):
        """Full optimistic flow: assumed value shown, then real device value after update."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox

        # Before set: real value
        assert min_entity.native_value == 8.0

        # After optimistic set: assumed value shown
        min_entity._assumed_value = 7.0
        assert min_entity.native_value == 7.0
        assert min_entity.assumed_state is True

        # Device confirmed: coordinator returns new value, assumed clears
        mock_wallbox.currents.min = 7
        with patch.object(min_entity, "async_write_ha_state"):
            min_entity._handle_coordinator_update()

        assert min_entity._assumed_value is None
        assert min_entity.native_value == 7.0

    def test_optimistic_flow_rejected_by_device(self, min_entity, mock_coordinator, mock_wallbox):
        """If the device rejects the change, the real value is shown after the update."""
        mock_coordinator.get_wallbox.return_value = mock_wallbox

        # Optimistic set to 7, but device still has 8
        min_entity._assumed_value = 7.0
        assert min_entity.native_value == 7.0

        # Device did not accept: coordinator still returns 8
        with patch.object(min_entity, "async_write_ha_state"):
            min_entity._handle_coordinator_update()

        assert min_entity._assumed_value is None
        assert min_entity.native_value == 8.0  # reverted

    def test_is_number_entity(self, min_entity):
        from homeassistant.components.number import NumberEntity
        assert isinstance(min_entity, NumberEntity)

    def test_device_class(self, min_entity):
        from homeassistant.components.number import NumberDeviceClass
        assert min_entity._attr_device_class == NumberDeviceClass.CURRENT

    def test_unit_of_measurement(self, min_entity):
        from homeassistant.const import UnitOfElectricCurrent
        assert min_entity._attr_native_unit_of_measurement == UnitOfElectricCurrent.AMPERE
