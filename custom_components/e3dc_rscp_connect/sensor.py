"Sensors of the E3DC rscp connect integration."

import logging

from homeassistant.core import HomeAssistant

# from homeassistant.helpers
from . import const
from .coordinator import E3dcRscpCoordinator
from .entities import (
    CpStateSensor,
    DeviceStateSensor,
    DeviceUpdateStateSensor,
    EmergencyPowerSensor,
    EnergySensor,
    PercentageSensor,
    PowerSensor,
    SGReadySensor,
    StateOfChargeSensor,
    WallboxPowerSensor,
)
from .e3dc_rscp_api import PM_TYPE_ADDITIONAL_CONSUMPTION, DeviceState

DOMAIN = const.DOMAIN
_LOGGER = logging.getLogger(__name__)


def get_total_production_power(coordinator: E3dcRscpCoordinator):
    """Sum of the internal PV power and the power of the additional generators.

    Returns None while neither value has been read from the device yet; a single
    missing value is treated as 0 so the sum stays usable.
    """
    powers = coordinator.storage.powers
    values = [value for value in (powers.pv, powers.additional) if value is not None]
    if not values:
        return None
    return sum(values)


def get_additional_consumption_power(coordinator: E3dcRscpCoordinator):
    """Sum of the power reported by every "additional consumption" powermeter.

    These are the CT clamps E3DC's own app/portal shows as separate
    consumers (e.g. a heat pump) under "Zusatzmessung" / "additional
    consumption" - distinct from the "additional generators" TAG_EMS_POWER_ADD
    tag (see powers.additional above), which is a second production source
    and unrelated to these CT clamps.

    Returns None until at least one such powermeter has been identified.
    """
    values = [
        pm.power
        for pm in coordinator.storage.powermeters.values()
        if pm.type == PM_TYPE_ADDITIONAL_CONSUMPTION and pm.power is not None
    ]
    if not values:
        return None
    return sum(values)


def get_inverter_mppt_power(
    coordinator: E3dcRscpCoordinator, inverter: int, mppt_index: int
):
    """This is a helper function, to return the MPPT power of a inverter."""
    _inverter = coordinator.storage.inverters.get(inverter, None)
    if _inverter is None:
        return None
    return _inverter.power_mppt.get(mppt_index, None)


async def async_setup_entry(
    hass: HomeAssistant, config_entry, async_add_entities
) -> None:
    "Setup the integration using config entry."

    coordinator: E3dcRscpCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    sensors = [
        PowerSensor(
            coordinator,
            config_entry,
            "Home Power",
            data_getter=lambda: coordinator.storage.powers.home,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Home Consumption",
            data_getter=lambda: coordinator.storage.powers.home,
        ),
        #
        # grid sensors
        PowerSensor(
            coordinator,
            config_entry,
            "Grid Power",
            data_getter=lambda: coordinator.storage.powers.grid,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Grid Consumption Energy",
            data_getter=lambda: coordinator.storage.powers.grid,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Grid Production Energy",
            data_getter=lambda: coordinator.storage.powers.grid,
            negative_direction=True,
        ),
        #
        # battery sensors
        PowerSensor(
            coordinator,
            config_entry,
            "Battery Power",
            data_getter=lambda: coordinator.storage.powers.battery,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Battery Charge Energy",
            data_getter=lambda: coordinator.storage.powers.battery,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Battery Discharge Energy",
            data_getter=lambda: coordinator.storage.powers.battery,
            negative_direction=True,
        ),
        #
        # PV sensors
        PowerSensor(
            coordinator,
            config_entry,
            "PV Power",
            data_getter=lambda: coordinator.storage.powers.pv,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "PV Production Energy",
            data_getter=lambda: coordinator.storage.powers.pv,
        ),
        #
        # Additional generators
        PowerSensor(
            coordinator,
            config_entry,
            "Additional Power",
            data_getter=lambda: coordinator.storage.powers.additional,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Additional Production Energy",
            data_getter=lambda: coordinator.storage.powers.additional,
        ),
        #
        # Additional consumption powermeters (CT clamps on individual loads,
        # e.g. a heat pump) - distinct from the "additional generators" pair
        # above, which is a different EMS tag.
        PowerSensor(
            coordinator,
            config_entry,
            "Additional Consumption Power",
            data_getter=lambda: get_additional_consumption_power(coordinator),
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Additional Consumption Energy",
            data_getter=lambda: get_additional_consumption_power(coordinator),
        ),
        #
        # Combined production of the internal inverter and the additional generators
        PowerSensor(
            coordinator,
            config_entry,
            "Total Production Power",
            data_getter=lambda: get_total_production_power(coordinator),
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Total Production Energy",
            data_getter=lambda: get_total_production_power(coordinator),
        ),
        #
        # Wallbox sensors (EMS)
        PowerSensor(
            coordinator,
            config_entry,
            "Wallbox Power",
            data_getter=lambda: coordinator.storage.powers.wallbox,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Wallbox Charge Energy",
            data_getter=lambda: coordinator.storage.powers.wallbox,
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "Wallbox PV Power",
            data_getter=lambda: coordinator.storage.powers.wallbox_pv,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Wallbox Sun Charge Energy",
            data_getter=lambda: coordinator.storage.powers.wallbox_pv,
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV String 1",
            data_getter=lambda: get_inverter_mppt_power(coordinator, 0, 0),
            # sensor_value_id="pvi_0_mppt_0_power",
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV String 2",
            data_getter=lambda: get_inverter_mppt_power(coordinator, 0, 1),
            # sensor_value_id="pvi_0_mppt_1_power",
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV String 3",
            data_getter=lambda: get_inverter_mppt_power(coordinator, 0, 2),
            # sensor_value_id="pvi_0_mppt_2_power",
        ),
        EmergencyPowerSensor(coordinator, config_entry),
        DeviceStateSensor(
            coordinator,
            config_entry,
            "Battery",
            lambda: coordinator.storage.device_states.battery.get(0, DeviceState()),
            0,
        ),
        DeviceUpdateStateSensor(
            coordinator,
            config_entry,
            "Battery",
            lambda: coordinator.storage.device_states.battery.get(0, DeviceState()),
            0,
        ),
        # DeviceStateSensor(
        #     coordinator,
        #     config_entry,
        #     "Battery",
        #     lambda: coordinator.storage.device_states.battery[1],
        #     1,
        # ),
        # DeviceUpdateStateSensor(
        #     coordinator,
        #     config_entry,
        #     "Battery",
        #     lambda: coordinator.storage.device_states.battery[1],
        #     1,
        # ),
        StateOfChargeSensor(coordinator, config_entry),
        PercentageSensor(
            coordinator,
            config_entry,
            "Autarky",
            data_getter=lambda: coordinator.storage.autarky,
        ),
        PercentageSensor(
            coordinator,
            config_entry,
            "Self Consumption",
            data_getter=lambda: coordinator.storage.self_consumption,
        ),
        SGReadySensor(coordinator, config_entry),
        *[
            CpStateSensor(coordinator, config_entry, wallbox.index, wallbox)
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxPowerSensor(
                coordinator,
                config_entry,
                "Assigned power",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.assigned_power,
            )
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxPowerSensor(
                coordinator,
                config_entry,
                "Current power",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.power,
            )
            for wallbox in coordinator.wallboxes
        ],
    ]

    async_add_entities(sensors)
