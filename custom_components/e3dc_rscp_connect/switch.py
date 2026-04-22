"""Switch entities for e3dc_rscp_connect."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import BatteryRemoteSwitch

DOMAIN = const.DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""

    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    async_add_entities([BatteryRemoteSwitch(coordinator, config_entry)])
