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
