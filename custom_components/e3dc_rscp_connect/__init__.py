"""e3dc_rscp_connect is a home assistant integration to provide data connector to E3DC storage systems."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import const
from .coordinator import E3dcRscpCoordinator
from rscp_lib.RscpConnection import RscpConnectionException

DOMAIN = const.DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Sets up the integration from config entry."""
    try:
        coordinator = E3dcRscpCoordinator(hass, entry)
        await coordinator.client.client.connect()

        await coordinator.async_config_entry_first_refresh()
    except RscpConnectionException as err:
        raise ConfigEntryNotReady(f"Error establishing the connection {err}") from err

    # Speichere den Koordinator zentral
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            entry, ["sensor", "select", "number", "switch"]
        )
    )

    _LOGGER.debug("Setup done for entry id: %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    "Used to perpare unloading of the integration."
    _LOGGER.debug("Unloading entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    await coordinator.stop_remote_control()
    coordinator.client.client.disconnect()

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "select", "number", "switch"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
