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
class SystemStatusModel:
    """The bits of the EMS system status register (TAG_EMS_SYS_STATUS).

    Every flag stays None until the register has been read, so a storage that
    does not answer the tag can be told apart from one that reports all bits
    as cleared.
    """

    raw: int | None = None

    battery_charging_locked: bool | None = None  # bit 0
    battery_discharging_locked: bool | None = None  # bit 1
    emergency_power_possible: bool | None = None  # bit 2
    weather_based_charging: bool | None = None  # bit 3
    power_derated: bool | None = None  # bit 4
    charge_lock_time_active: bool | None = None  # bit 5
    discharge_lock_time_active: bool | None = None  # bit 6


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

    system_status: SystemStatusModel = field(default_factory=SystemStatusModel)

    inverters: dict[int, PvInverterData] = field(default_factory=dict)
