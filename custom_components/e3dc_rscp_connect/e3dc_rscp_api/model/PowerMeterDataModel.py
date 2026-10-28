"This file contains the PowerMeterDataModel."

from dataclasses import dataclass
from enum import IntEnum


class PowerMeterType(IntEnum):
    "The power meter roles as reported by the storage in TAG_PM_TYPE."

    UNDEFINED = 0
    ROOT = 1
    ADDITIONAL = 2
    ADDITIONAL_PRODUCTION = 3
    ADDITIONAL_CONSUMPTION = 4
    FARM = 5
    UNUSED = 6
    WALLBOX = 7
    FARM_ADDITIONAL = 8
    ALIEN = 9
    REGULATOR_BYPASS = 10
    NO_CHARGE_METER = 11



@dataclass
class PowerMeterDataModel:
    "PowerMeterDataModel represents one of the power meters known to the storage."

    index: int
    power_l1: float | None = None
    power_l2: float | None = None
    power_l3: float | None = None
    voltage_l1: float | None = None
    voltage_l2: float | None = None
    voltage_l3: float | None = None

    # identification data:
    # a PowerMeterType, or the raw number for a type this package does not know yet
    pm_type: PowerMeterType | int | None = None
    # the name configured for the meter on the storage
    device_name: str | None = None

    @property
    def power(self) -> float | None:
        "Sum of the phases that have been read, None while none has."
        phases = [p for p in (self.power_l1, self.power_l2, self.power_l3) if p is not None]
        if not phases:
            return None
        return sum(phases)

    def reset_state_data(self):
        "Resets only the state data, the device identification data stays."
        self.power_l1 = None
        self.power_l2 = None
        self.power_l3 = None
        self.voltage_l1 = None
        self.voltage_l2 = None
        self.voltage_l3 = None
