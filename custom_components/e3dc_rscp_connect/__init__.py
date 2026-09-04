"""e3dc_rscp_connect is a home assistant integration to provide data connector to E3DC storage systems."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from . import const
from .coordinator import E3dcRscpCoordinator
from .e3dc_rscp_api import (
    E3dcAuthenticationError,
    E3dcIdentificationError,
    E3dcRscpError,
)

DOMAIN = const.DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Sets up the integration from config entry."""
    try:
        coordinator = E3dcRscpCoordinator(hass, entry)
        await coordinator.async_connect()

        await coordinator.async_config_entry_first_refresh()
    except (E3dcAuthenticationError, E3dcIdentificationError) as err:
        # Retrying with the same wrong credentials is pointless, ask the user
        # for new ones instead. Home Assistant starts the reauth flow for this.
        raise ConfigEntryAuthFailed(str(err)) from err
    except E3dcRscpError as err:
        raise ConfigEntryNotReady(f"Error establishing the connection {err}") from err

    # Reload the entry when the options change, otherwise the coordinator keeps
    # running with the credentials it was created with.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

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


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    "Reloads the entry after its configuration was changed."
    _LOGGER.debug("Configuration changed, reloading entry: %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    "Used to perpare unloading of the integration."
    _LOGGER.debug("Unloading entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    await coordinator.stop_remote_control()
    coordinator.disconnect()

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "select", "number", "switch"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
