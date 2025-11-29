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
class StorageDataModel:
    "The dataclass holding the information."

    # identification data:
    serial: str | None = None
    assembly_serial: str | None = None
    mac_addr: str | None = None
    sw_version: str | None = None

    powers: EmsPowerModel = field(default_factory=lambda: EmsPowerModel())

    # power data
    bat_soc: int | None = None

    emergency_power_state: int | None = None
