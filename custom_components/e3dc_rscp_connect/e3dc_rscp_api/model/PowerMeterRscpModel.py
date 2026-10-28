"This file contains PowerMeterRscpModel. A class to read the power meters of a storage system through RSCP."

import logging

from rscp_lib.RscpValue import RscpValue
from .PowerMeterDataModel import PowerMeterDataModel, PowerMeterType
from .RscpModelInterface import RscpModelInterface

logger = logging.getLogger(__name__)

# The E3/DC software knows this many power meter slots.
POWER_METER_SLOTS = 8

# Slots the storage reports, but that have no meter behind them.
_NOT_EQUIPPED = (PowerMeterType.UNDEFINED, PowerMeterType.UNUSED)


def _value(container: RscpValue, tag_name: str):
    "Returns the value of a child tag, None if it is missing or an error."
    value = container.get_child(tag_name)
    if value is None or getattr(value, "isError", False):
        return None
    return value.getValue()


class PowerMeterRscpModel(RscpModelInterface):
    "This class represents the RSCP communication with a power meter and stores the data in a PowerMeterDataModel."

    def __init__(
        self,
        index: int,
        pm_type: PowerMeterType | int | None = None,
        device_name: str | None = None,
    ) -> None:
        "Inits the PowerMeterRscpModel for slot index."
        self.__index = index
        self.__model = PowerMeterDataModel(index)
        self.__model.pm_type = pm_type
        self.__model.device_name = device_name

    def __eq__(self, other):
        "Power meters have no serial, the slot identifies them."
        if not isinstance(other, PowerMeterRscpModel):
            return NotImplemented
        return self.index == other.index

    def __hash__(self):
        return hash(self.index)

    def get_model(self) -> PowerMeterDataModel:
        "Returns the data model."
        return self.__model

    @property
    def index(self) -> int:
        return self.__index

    @staticmethod
    def get_identification_tags() -> list[RscpValue]:
        """Returns a list of RscpTags to identify power meters!"""
        return [
            RscpValue.construct_rscp_value(
                "TAG_PM_REQ_DATA",
                [
                    ("TAG_PM_INDEX", index),
                    ("TAG_PM_REQ_TYPE", None),
                    ("TAG_PM_REQ_DEVICE_NAME", None),
                ],
            )
            for index in range(POWER_METER_SLOTS)
        ]

    @staticmethod
    def identify(container: RscpValue) -> RscpModelInterface | None:
        """Tries to identify a power meter. Input should be a container of type: TAG_PM_DATA."""
        if container.getTagName() != "TAG_PM_DATA":
            return None

        index = _value(container, "TAG_PM_INDEX")
        raw_type = _value(container, "TAG_PM_TYPE")
        if index is None or raw_type is None:
            return None

        try:
            pm_type = PowerMeterType(raw_type)
        except ValueError:
            logger.info("Unknown power meter type %s at index %d", raw_type, index)
            pm_type = raw_type

        if pm_type in _NOT_EQUIPPED:
            logger.debug("Power meter slot %d not equipped (%s)", index, pm_type)
            return None

        # an empty name is treated like none being configured
        device_name = _value(container, "TAG_PM_DEVICE_NAME") or None
        return PowerMeterRscpModel(index, pm_type, device_name)

    def get_rscp_tags(self) -> list[RscpValue]:
        "Returns all tags used to get informations from device!"
        return [
            RscpValue.construct_rscp_value(
                "TAG_PM_REQ_DATA",
                [
                    ("TAG_PM_INDEX", self.__index),
                    ("TAG_PM_REQ_POWER_L1", None),
                    ("TAG_PM_REQ_POWER_L2", None),
                    ("TAG_PM_REQ_POWER_L3", None),
                    ("TAG_PM_REQ_VOLTAGE_L1", None),
                    ("TAG_PM_REQ_VOLTAGE_L2", None),
                    ("TAG_PM_REQ_VOLTAGE_L3", None),
                ],
            )
        ]

    def get_rscp_tags_slow(self):
        pass

    def handle_rscp_data(self, container: RscpValue) -> bool:
        "This function is used to retrieve data from a rscp tag!"
        if container.getTagName() != "TAG_PM_DATA":
            return False

        # check if data in container is targeted for our index!
        if _value(container, "TAG_PM_INDEX") != self.__index:
            return False

        self.__model.reset_state_data()
        self.__model.power_l1 = _value(container, "TAG_PM_POWER_L1")
        self.__model.power_l2 = _value(container, "TAG_PM_POWER_L2")
        self.__model.power_l3 = _value(container, "TAG_PM_POWER_L3")
        self.__model.voltage_l1 = _value(container, "TAG_PM_VOLTAGE_L1")
        self.__model.voltage_l2 = _value(container, "TAG_PM_VOLTAGE_L2")
        self.__model.voltage_l3 = _value(container, "TAG_PM_VOLTAGE_L3")
        return True
