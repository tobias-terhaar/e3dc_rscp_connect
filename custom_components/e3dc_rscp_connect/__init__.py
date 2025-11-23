"""e3dc_rscp_connect is a home assistant integration to provide data connector to E3DC storage systems."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import const
from .coordinator import E3dcRscpCoordinator
from .e3dc.RscpConnection import RscpConnectionException

DOMAIN = const.DOMAIN


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
        hass.config_entries.async_forward_entry_setups(entry, ["sensor", "select"])
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    "Used to perpare unloading of the integration."
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "select"]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
