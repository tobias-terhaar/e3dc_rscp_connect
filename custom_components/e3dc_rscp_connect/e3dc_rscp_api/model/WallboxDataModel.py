"This file contains the WallboxDataModel."

from dataclasses import dataclass, field
from enum import IntEnum


class WallboxType(IntEnum):
    "The wallbox models as reported by the storage in TAG_WB_WALLBOX_TYPE."

    E3DC = 1
    EASY = 2
    EDISON = 5
    MULTI = 6
    EFY = 8
    EDSN = 11


@dataclass
class WallboxCurrentModel:
    upper_limit: int = 0
    lower_limit: int = 0
    max: int = 0
    min: int = 0


@dataclass
class WallboxDataModel:
    "WallboxDataModel represents a wallbox."

    index: int
    cp_state: str | None = None
    assigned_power: int | None = None
    power: int | None = None
    available_solar_power: int | None = None
    sun_mode: bool | None = None
    currents: WallboxCurrentModel = field(default_factory=WallboxCurrentModel)

    # identification data:
    serial: str | None = None
    device_name: str | None = None
    firmware_version: str | None = None
    # a WallboxType, or the raw number for a type this package does not know yet
    wallbox_type: WallboxType | int | None = None

    def reset_state_data(self):
        "Resets only the state data, the device identification data stays."
        self.cp_state = None
        self.assigned_power = None
        self.power = None
        self.available_solar_power = None
        self.sun_mode = None
