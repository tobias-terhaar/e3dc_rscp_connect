"This file contains the WallboxDataModel."

from dataclasses import dataclass


@dataclass
class WallboxDataModel:
    "WallboxDataModel represents a wallbox."

    index: int
    cp_state: str | None = None
    assigned_power: int | None = None
    power: int | None = None
    sun_mode: bool | None = None

    # identification data:
    serial: str | None = None
    device_name: str | None = None
    firmware_version: str | None = None

    def reset_state_data(self):
        "Resets only the state data, the device identification data stays."
        self.cp_state = None
        self.assigned_power = None
        self.power = None
        self.sun_mode = None
