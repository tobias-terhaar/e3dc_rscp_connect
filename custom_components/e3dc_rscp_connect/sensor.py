"Sensors of the E3DC rscp connect integration."

import logging

from homeassistant.core import HomeAssistant

from . import const
from .entities import CpStateSensor, EnergySensor, PowerSensor, StateOfChargeSensor

DOMAIN = const.DOMAIN
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
) -> None:
    "Setup the integration using config entry."

    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

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
        PowerSensor(
            coordinator, config_entry, "PVI 0 MPPT 0 Power", "pvi_0_mppt_0_power"
        ),
        PowerSensor(
            coordinator, config_entry, "PVI 0 MPPT 1 Power", "pvi_0_mppt_1_power"
        ),
        PowerSensor(
            coordinator, config_entry, "PVI 0 MPPT 2 Power", "pvi_0_mppt_2_power"
        ),
        # wallboxes
        CpStateSensor(coordinator, config_entry, 0),
        PowerSensor(
            coordinator,
            config_entry,
            "WB 0 Assigned Power",
            "wb_0_assigned_power",
            "Wallbox",
            0,
        ),
        CpStateSensor(coordinator, config_entry, 1),
        PowerSensor(
            coordinator,
            config_entry,
            "WB 1 Assigned Power",
            "wb_1_assigned_power",
            "Wallbox",
            1,
        ),
        StateOfChargeSensor(coordinator, config_entry),
    ]

    async_add_entities(sensors)
