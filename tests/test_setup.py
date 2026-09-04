"""Tests for the setup of a config entry and its error handling."""

from pathlib import Path
import sys

custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import pytest

from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from e3dc_rscp_connect import async_reload_entry, async_setup_entry
from e3dc_rscp_connect.coordinator import E3dcRscpCoordinator
from e3dc_rscp_connect.e3dc_rscp_api import (
    E3dcAuthenticationError,
    E3dcConnectionError,
    E3dcIdentificationError,
    E3dcRscpError,
)


def make_hass():
    def create_task(coro, *args, **kwargs):
        # Nothing runs the task here, close the coroutine to keep it quiet.
        coro.close()
        return Mock()

    hass = Mock()
    hass.data = {}
    hass.async_create_task = Mock(side_effect=create_task)
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    hass.config_entries.async_reload = AsyncMock()
    return hass


def make_entry():
    entry = Mock(entry_id="entry-1")
    entry.async_on_unload = Mock()
    entry.add_update_listener = Mock(return_value="unsubscribe")
    return entry


def patch_coordinator(coordinator):
    return patch(
        "e3dc_rscp_connect.E3dcRscpCoordinator",
        return_value=coordinator,
    )


def make_coordinator(connect_error=None):
    coordinator = Mock()
    coordinator.async_connect = AsyncMock(side_effect=connect_error)
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator


def make_bare_coordinator(fetch_error):
    """A coordinator with just enough state to run _async_update_data."""
    coordinator = object.__new__(E3dcRscpCoordinator)
    coordinator._E3dcRscpCoordinator__last_device_info_update = datetime.now(UTC)
    coordinator._E3dcRscpCoordinator__device_info_interval = timedelta(minutes=60)
    coordinator.client = Mock(fetch_data=AsyncMock(side_effect=fetch_error))
    return coordinator


# ─────────────────────────────────────────────────────────────────────────────
# Setup error handling
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "error",
    [
        E3dcAuthenticationError("wrong password"),
        E3dcIdentificationError("wrong rscp key"),
    ],
)
@pytest.mark.asyncio
async def test_rejected_credentials_ask_for_reauthentication(error):
    """Retrying with the same wrong credentials would never succeed."""
    hass, entry = make_hass(), make_entry()

    with patch_coordinator(make_coordinator(connect_error=error)):
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_unreachable_device_is_retried():
    hass, entry = make_hass(), make_entry()

    with patch_coordinator(make_coordinator(connect_error=E3dcConnectionError("down"))):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_other_api_errors_are_retried():
    hass, entry = make_hass(), make_entry()

    with patch_coordinator(make_coordinator(connect_error=E3dcRscpError("odd"))):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)


# ─────────────────────────────────────────────────────────────────────────────
# Reload on configuration change
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setup_listens_for_configuration_changes():
    """Without this the coordinator keeps the credentials it was built with."""
    hass, entry = make_hass(), make_entry()
    coordinator = make_coordinator()

    with patch_coordinator(coordinator):
        assert await async_setup_entry(hass, entry) is True

    entry.add_update_listener.assert_called_once_with(async_reload_entry)
    entry.async_on_unload.assert_called_once_with("unsubscribe")


@pytest.mark.asyncio
async def test_changed_configuration_reloads_the_entry():
    hass, entry = make_hass(), make_entry()

    await async_reload_entry(hass, entry)

    hass.config_entries.async_reload.assert_awaited_once_with("entry-1")


# ─────────────────────────────────────────────────────────────────────────────
# Errors while polling
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "error",
    [
        E3dcAuthenticationError("password changed on the device"),
        E3dcIdentificationError("rscp key changed on the device"),
    ],
)
@pytest.mark.asyncio
async def test_credentials_rejected_while_polling_ask_for_reauthentication(error):
    coordinator = make_bare_coordinator(error)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_other_errors_while_polling_are_update_failures():
    coordinator = make_bare_coordinator(E3dcConnectionError("connection lost"))

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
