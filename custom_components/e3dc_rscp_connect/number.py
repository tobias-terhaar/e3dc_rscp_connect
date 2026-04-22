"""Number entities for e3dc_rscp_connect."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import BatteryRemotePowerNumber, WallboxMaxCurrentNumber, WallboxMinCurrentNumber

DOMAIN = const.DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""

    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    numbers = [
        BatteryRemotePowerNumber(coordinator, config_entry),
        *[
            WallboxMaxCurrentNumber(coordinator, config_entry, wallbox)
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxMinCurrentNumber(coordinator, config_entry, wallbox)
            for wallbox in coordinator.wallboxes
        ],
    ]

    async_add_entities(numbers)
