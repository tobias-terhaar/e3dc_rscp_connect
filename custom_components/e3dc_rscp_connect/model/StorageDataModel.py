"""Data class to hold all data about a storage system."""

from dataclasses import dataclass, field


@dataclass
class EmsPowerModel:
    "Holding power values delivered by EMS tags."

    home: int = 0
    battery: int = 0
    grid: int = 0
    pv: int = 0
    additional: int = 0
    wallbox: int = 0
    wallbox_pv: int = 0


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
    bat_soc: int = 0

    emergency_power_state: int = 0
