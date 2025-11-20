from homeassistant.core import HomeAssistant

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import SunModeSensor

DOMAIN = const.DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
) -> None:
    "Setup the integration using config entry."

    # get the coordinator from hass data
    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    selects = [
        *[
            SunModeSensor(
                coordinator, config_entry, x, coordinator.get_wallbox_ident(x)
            )
            for x in coordinator.wb_indexes
        ],
    ]

    async_add_entities(selects)
