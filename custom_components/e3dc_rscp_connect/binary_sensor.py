"Binary sensors of the E3DC rscp connect integration."

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import SystemStatusBinarySensor

DOMAIN = const.DOMAIN
_LOGGER = logging.getLogger(__name__)

# The bits of the EMS system status register and the name they get in HA.
SYSTEM_STATUS_SENSORS = (
    ("Battery Charging Locked", "battery_charging_locked"),
    ("Battery Discharging Locked", "battery_discharging_locked"),
    ("Emergency Power Possible", "emergency_power_possible"),
    ("Weather Based Charging", "weather_based_charging"),
    ("Power Derated", "power_derated"),
    ("Charge Lock Time Active", "charge_lock_time_active"),
    ("Discharge Lock Time Active", "discharge_lock_time_active"),
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
        SystemStatusBinarySensor(coordinator, config_entry, name, status_field)
        for name, status_field in SYSTEM_STATUS_SENSORS
    )
