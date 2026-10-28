"Binary sensors of the E3DC rscp connect integration."

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import SystemStatusBinarySensor

DOMAIN = const.DOMAIN
_LOGGER = logging.getLogger(__name__)

# The flags of the EMS system status register shown in HA. Each field name is
# also the translation key of the sensor's name.
SYSTEM_STATUS_SENSORS = (
    "pv_derated",
    "power_save_enabled",
    "charge_idle_period_active",
    "discharge_idle_period_active",
    "wait_for_weather_breakthrough",
    "emergency_reserve_reached",
    "idle_periods_enabled",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    "Set up the binary sensor platform."

    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    async_add_entities(
        SystemStatusBinarySensor(coordinator, config_entry, status_field)
        for status_field in SYSTEM_STATUS_SENSORS
    )
