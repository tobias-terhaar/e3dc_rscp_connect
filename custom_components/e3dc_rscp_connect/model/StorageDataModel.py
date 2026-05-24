"""Data class to hold all data about a storage system."""

from dataclasses import dataclass, field


@dataclass
class EmsPowerModel:
    "Holding power values delivered by EMS tags."

    home: int | None = None
    battery: int | None = None
    grid: int | None = None
    pv: int | None = None
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
