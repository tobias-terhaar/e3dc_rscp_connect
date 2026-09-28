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
    WallboxDailyEnergySensor,
    WallboxEnergySensor,
    WallboxPowerSensor,
    WallboxSessionEnergySensor,
)
from .e3dc_rscp_api import DeviceState

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
            "Home power",
            key="home_power",
            data_getter=lambda: coordinator.storage.powers.home,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Home consumption energy",
            key="home_consumption",
            data_getter=lambda: coordinator.storage.powers.home,
        ),
        #
        # grid sensors
        PowerSensor(
            coordinator,
            config_entry,
            "Grid power",
            key="grid_power",
            data_getter=lambda: coordinator.storage.powers.grid,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Grid consumption energy",
            key="grid_consumption_energy",
            data_getter=lambda: coordinator.storage.powers.grid,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Grid production energy",
            key="grid_production_energy",
            data_getter=lambda: coordinator.storage.powers.grid,
            negative_direction=True,
        ),
        #
        # battery sensors
        PowerSensor(
            coordinator,
            config_entry,
            "Battery power",
            key="battery_power",
            data_getter=lambda: coordinator.storage.powers.battery,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Battery charge energy",
            key="battery_charge_energy",
            data_getter=lambda: coordinator.storage.powers.battery,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Battery discharge energy",
            key="battery_discharge_energy",
            data_getter=lambda: coordinator.storage.powers.battery,
            negative_direction=True,
        ),
        #
        # PV sensors
        PowerSensor(
            coordinator,
            config_entry,
            "PV power",
            key="pv_power",
            data_getter=lambda: coordinator.storage.powers.pv,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "PV production energy",
            key="pv_production_energy",
            data_getter=lambda: coordinator.storage.powers.pv,
        ),
        #
        # Additional generators
        PowerSensor(
            coordinator,
            config_entry,
            "Additional generators power",
            key="additional_power",
            data_getter=lambda: coordinator.storage.powers.additional,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Additional generators energy",
            key="additional_production_energy",
            data_getter=lambda: coordinator.storage.powers.additional,
        ),
        #
        # Combined production of the internal inverter and the additional generators
        PowerSensor(
            coordinator,
            config_entry,
            "Total production power",
            key="total_production_power",
            data_getter=lambda: get_total_production_power(coordinator),
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Total production energy",
            key="total_production_energy",
            data_getter=lambda: get_total_production_power(coordinator),
        ),
        #
        # Wallbox sensors (EMS)
        PowerSensor(
            coordinator,
            config_entry,
            "Wallbox power",
            key="wallbox_power",
            data_getter=lambda: coordinator.storage.powers.wallbox,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Wallbox charge energy",
            key="wallbox_charge_energy",
            data_getter=lambda: coordinator.storage.powers.wallbox,
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "Wallbox PV power",
            key="wallbox_pv_power",
            data_getter=lambda: coordinator.storage.powers.wallbox_pv,
        ),
        EnergySensor(
            coordinator,
            config_entry,
            "Wallbox PV charge energy",
            key="wallbox_sun_charge_energy",
            data_getter=lambda: coordinator.storage.powers.wallbox_pv,
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV string 1",
            key="pv_string_1",
            data_getter=lambda: get_inverter_mppt_power(coordinator, 0, 0),
            # sensor_value_id="pvi_0_mppt_0_power",
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV string 2",
            key="pv_string_2",
            data_getter=lambda: get_inverter_mppt_power(coordinator, 0, 1),
            # sensor_value_id="pvi_0_mppt_1_power",
        ),
        PowerSensor(
            coordinator,
            config_entry,
            "PV string 3",
            key="pv_string_3",
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
            key="autarky",
            data_getter=lambda: coordinator.storage.autarky,
        ),
        PercentageSensor(
            coordinator,
            config_entry,
            "Self consumption",
            key="self_consumption",
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
                key="assigned_power",
            )
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxPowerSensor(
                coordinator,
                config_entry,
                "Charging power",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.power,
                key="current_power",
            )
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxEnergySensor(
                coordinator,
                config_entry,
                "Charged energy",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.power,
                key="total_charged_energy",
            )
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxDailyEnergySensor(
                coordinator,
                config_entry,
                "Charged energy today",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.power,
                key="daily_charged_energy",
            )
            for wallbox in coordinator.wallboxes
        ],
        *[
            WallboxSessionEnergySensor(
                coordinator,
                config_entry,
                "Charged energy this session",
                wallbox.index,
                lambda wallbox=wallbox: wallbox.power,
                lambda wallbox=wallbox: wallbox.cp_state,
                key="session_charged_energy",
            )
            for wallbox in coordinator.wallboxes
        ],
    ]

    async_add_entities(sensors)
