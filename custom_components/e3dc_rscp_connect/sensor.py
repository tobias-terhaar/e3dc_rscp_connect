"Sensors of the E3DC rscp connect integration."

import logging

from homeassistant.core import HomeAssistant

from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import (
    CpStateSensor,
    EmergencyPowerSensor,
    EnergySensor,
    PowerSensor,
    StateOfChargeSensor,
    SunModeSensor,
)

DOMAIN = const.DOMAIN
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
) -> None:
    "Setup the integration using config entry."

    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    sensors = [
        PowerSensor(coordinator, config_entry, "Home Power", "home_power"),
        EnergySensor(coordinator, config_entry, "Home Consumption", "home_power"),
        #
        # grid sensors
        PowerSensor(coordinator, config_entry, "Grid Power", "grid_power"),
        EnergySensor(
            coordinator, config_entry, "Grid Consumption Energy", "grid_power"
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Grid Production Energy",
            "grid_power",
            negative_direction=True,
        ),
        #
        # battery sensors
        PowerSensor(coordinator, config_entry, "Battery Power", "battery_power"),
        EnergySensor(
            coordinator, config_entry, "Battery Charge Energy", "battery_power"
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Battery Discharge Energy",
            "battery_power",
            negative_direction=True,
        ),
        #
        # PV sensors
        PowerSensor(coordinator, config_entry, "PV Power", "pv_power"),
        EnergySensor(coordinator, config_entry, "PV Production Energy", "pv_power"),
        #
        # Additional generators
        PowerSensor(coordinator, config_entry, "Additional Power", "additional_power"),
        EnergySensor(
            coordinator,
            config_entry,
            "Additional Production Energy",
            "additional_power",
        ),
        #
        # Wallbox sensors (EMS)
        PowerSensor(coordinator, config_entry, "Wallbox Power", "wallbox_power"),
        EnergySensor(
            coordinator, config_entry, "Wallbox Charge Energy", "wallbox_power"
        ),
        PowerSensor(coordinator, config_entry, "Wallbox PV Power", "wallbox_pv_power"),
        EnergySensor(
            coordinator, config_entry, "Wallbox Sun Charge Energy", "wallbox_pv_power"
        ),
        PowerSensor(coordinator, config_entry, "PV String 1", "pvi_0_mppt_0_power"),
        PowerSensor(coordinator, config_entry, "PV String 2", "pvi_0_mppt_1_power"),
        PowerSensor(coordinator, config_entry, "PV String 3", "pvi_0_mppt_2_power"),
        EmergencyPowerSensor(coordinator, config_entry, "emergency_power_status"),
        StateOfChargeSensor(coordinator, config_entry),
        *[
            CpStateSensor(
                coordinator, config_entry, x, coordinator.get_wallbox_ident(x)
            )
            for x in coordinator.wb_indexes
        ],
        *[
            SunModeSensor(
                coordinator, config_entry, x, coordinator.get_wallbox_ident(x)
            )
            for x in coordinator.wb_indexes
        ],
        *[
            PowerSensor(
                coordinator,
                config_entry,
                "Zugewiesene Leistung",
                f"wb_{x}_assigned_power",
                "Wallbox",
                x,
            )
            for x in coordinator.wb_indexes
        ],
    ]

    async_add_entities(sensors)
