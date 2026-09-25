"""Data class to hold all data about a storage system."""

from dataclasses import dataclass, field


@dataclass
class EmsPowerModel:
    "Holding power values delivered by EMS tags."

    home: int | None = None
    battery: int | None = None
    grid: int | None = None
    pv: int | None = None
    # positive while the additional generators produce (the EMS reports it inverted)
    additional: int | None = None
    wallbox: int | None = None
    wallbox_pv: int | None = None


@dataclass
class DeviceState:
    "Data class to hold states of the storage devices."

    connected: bool = False
    working: bool = False
    in_service: bool = False


@dataclass
class DeviceStates:
    "Class to hold informations about all device states of the storage!"

    battery: dict[int, DeviceState] = field(default_factory=dict)
    inverter: dict[int, DeviceState] = field(default_factory=dict)
    powermeter: dict[int, DeviceState] = field(default_factory=dict)


@dataclass
class PvInverterData:
    "Class holds the power data of an inverter."

    power_mppt: dict[int, int | None] = field(default_factory=dict)


# E3DC powermeter "TAG_PM_TYPE" values observed in the wild. Only ROOT (the
# main grid meter, already covered by TAG_EMS_POWER_GRID) and
# ADDITIONAL_CONSUMPTION (extra CT clamps on individual loads, e.g. a heat
# pump) are relevant here; other values are stored but not interpreted.
PM_TYPE_ROOT = 1
PM_TYPE_ADDITIONAL_CONSUMPTION = 4


@dataclass
class PowerMeterData:
    "Class holds the data of one E3DC powermeter (a physical CT clamp)."

    type: int | None = None
    # Sum of TAG_PM_POWER_L1/L2/L3, in Watt. Positive = consumption on the
    # monitored circuit, matching the sign convention of the other power
    # values in this model.
    power: float | None = None


@dataclass
class StorageDataModel:
    "The dataclass holding the information."

    # identification data:
    serial: str | None = None
    assembly_serial: str | None = None
    mac_addr: str | None = None
    sw_version: str | None = None

    device_states: DeviceStates = field(default_factory=DeviceStates)

    powers: EmsPowerModel = field(default_factory=EmsPowerModel)

    # power data
    bat_soc: int | None = None

    autarky: float | None = None
    self_consumption: float | None = None

    emergency_power_state: int | None = None

    inverters: dict[int, PvInverterData] = field(default_factory=dict)

    powermeters: dict[int, PowerMeterData] = field(default_factory=dict)
