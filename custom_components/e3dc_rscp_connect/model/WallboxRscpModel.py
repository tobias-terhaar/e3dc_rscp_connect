"This file contains WallboxRscpModel. A class to communicate with the wallboxes through RSCP over an storage system."

import logging

from ..e3dc.RscpValue import RscpValue  # noqa: TID252
from .RscpModelInterface import RscpModelInterface
from .WallboxDataModel import WallboxDataModel

logger = logging.getLogger(__name__)


class WallboxRscpModel(RscpModelInterface):
    "This class represents the RSCP communication with a wallbox and stores the data in a WallboxDataModel."

    def __init__(
        self,
        wallbox_index: int,
        serial: str | None = None,
        device_name: str | None = None,
        firmware_version: str | None = None,
    ) -> None:
        "Inits the WalboxRscpModel for index wallbox_index."
        self.__index = wallbox_index
        self.__model = WallboxDataModel(wallbox_index)
        self.__model.serial = serial
        self.__model.device_name = device_name
        self.__model.firmware_version = firmware_version

    def __eq__(self, other):
        "Comparing two WallboxRscpModeöl instances."
        if not isinstance(other, WallboxRscpModel):
            return NotImplemented
        return self.serial == other.serial

    def __hash__(self):
        "Hashing the serial for comparisation."
        return hash(self.serial)

    def get_model(self) -> WallboxDataModel:
        "Returns the data model."
        return self.__model

    @property
    def index(self) -> int:
        return self.__index

    @property
    def serial(self) -> str:
        if self.__model == None:
            return ""
        return self.__model.serial

    @staticmethod
    def get_identification_tags() -> list[RscpValue]:
        """Returns a list of RscpTags to identify wallboxes!"""
        return [
            RscpValue.construct_rscp_value(
                "TAG_WB_REQ_DATA",
                [
                    ("TAG_WB_INDEX", index),
                    ("TAG_WB_REQ_SERIAL", None),
                    ("TAG_WB_REQ_DEVICE_NAME", None),
                    ("TAG_WB_REQ_FIRMWARE_VERSION", None),
                ],
            )
            for index in range(7)
        ]

    @staticmethod
    def identify(container: RscpValue) -> RscpModelInterface | None:
        """Tries to identify the wallbox. Input should be a container of type: TAG_WB_DATA."""
        if container.getTagName() != "TAG_WB_DATA":
            return None

        index = container.get_child("TAG_WB_INDEX")
        serial = container.get_child("TAG_WB_SERIAL")
        device_name = container.get_child("TAG_WB_DEVICE_NAME")
        firmware_version = container.get_child("TAG_WB_FIRMWARE_VERSION")
        # if we received a serial, then we found an valid wallbox
        if serial:
            index = index.getValue()
            return WallboxRscpModel(
                index,
                serial.getValue(),
                device_name.getValue(),
                firmware_version.getValue(),
            )
        return None

    def get_rscp_tags(self) -> list[RscpValue]:
        "Returns all tags used to get informations from device!"
        return [
            RscpValue.construct_rscp_value(
                "TAG_WB_REQ_DATA",
                [
                    ("TAG_WB_INDEX", self.__index),
                    ("TAG_WB_REQ_CP_STATE", None),
                    ("TAG_WB_REQ_PARAMETER_LIST", 0),
                    ("TAG_WB_REQ_PARAMETER_LIST", 1),
                    ("TAG_WB_REQ_ACTIVE_CHARGE_STRATEGY", None),
                    ("TAG_WB_REQ_ASSIGNED_POWER", None),
                    ("TAG_WB_REQ_PM_POWER_L1", None),
                    ("TAG_WB_REQ_PM_POWER_L2", None),
                    ("TAG_WB_REQ_PM_POWER_L3", None),
                    ("TAG_WB_REQ_DEVICE_STATE", None),
                    ("TAG_WB_REQ_SUN_MODE_ACTIVE", None),
                    ("TAG_WB_REQ_UPPER_CURRENT_LIMIT", None),
                    ("TAG_WB_REQ_LOWER_CURRENT_LIMIT", None),
                    ("TAG_WB_REQ_MAX_CHARGE_CURRENT", None),
                    ("TAG_WB_REQ_MIN_CHARGE_CURRENT", None),
                ],
            )
        ]

    def get_rscp_tags_slow(self):
        pass

    # def __extract_wallbox_data(self, container: RscpValue):
    def handle_rscp_data(self, container: RscpValue) -> bool:
        "This function is used to retrieve data from a rscp tag!"

        if container.getTagName() != "TAG_WB_DATA":
            return False

        wb_index = container.get_child("TAG_WB_INDEX")
        if wb_index is None:
            value = container.get_child("TAG_WB_REQ_INDEX")
            logger.warning(
                "No TAG_WB_INDEX in container, errorcode: %d", value.getValue()
            )
            return False

        wb_index = wb_index.getValue()
        # check if data in container is targeted for our index!
        if wb_index != self.__index:
            return False

        self.__model.reset_state_data()

        value = container.get_child("TAG_WB_CP_STATE")
        if value is None:
            logger.warning("CP State value is None for wb_index: %d", wb_index)
            self.__model.cp_state = None
        else:
            logger.debug("CP State: %s", value.toString())
            self.__model.cp_state = str(value.getValue())

        assigned_power_container = container.get_child("TAG_WB_ASSIGNED_POWER")
        if assigned_power_container:
            self.__model.assigned_power = sum(
                x.getValue() for x in assigned_power_container.getValue()
            )

        self.__model.power = self.__extract_power_from_wb_data(container)

        # power_container = container.get_child("TAG_WB_REQ_AVAILABLE_SOLAR_POWER")
        # if power_container:
        #     logger.debug("WB available solar power: %s", power_container.toString())
        #     self.__model.available_solar_power = sum(
        #         x.getValue() for x in power_container.getValue()
        #     )

        value = container.get_child("TAG_WB_SUN_MODE_ACTIVE")
        self.__model.sun_mode = value.getValue() if value is not None else None

        value = container.get_child("TAG_WB_UPPER_CURRENT_LIMIT")
        self.__model.currents.upper_limit = value.getValue() if value is not None else 0

        value = container.get_child("TAG_WB_LOWER_CURRENT_LIMIT")
        self.__model.currents.lower_limit = value.getValue() if value is not None else 0

        value = container.get_child("TAG_WB_MAX_CHARGE_CURRENT")
        self.__model.currents.max = value.getValue() if value is not None else 0

        value = container.get_child("TAG_WB_MIN_CHARGE_CURRENT")
        self.__model.currents.min = value.getValue() if value is not None else 0

        return True

    def __extract_power_from_wb_data(self, wb_data: RscpValue) -> int:
        power_total = 0
        power_l1 = wb_data.get_child("TAG_WB_PM_POWER_L1")
        if power_l1:
            logger.debug("WB POWER L1: %s", power_l1.toString())
            power_total += power_l1.getValue()

        power_l2 = wb_data.get_child("TAG_WB_PM_POWER_L3")
        if power_l2:
            logger.debug("WB POWER L2: %s", power_l2.toString())
            power_total += power_l2.getValue()

        power_l3 = wb_data.get_child("TAG_WB_PM_POWER_L3")
        if power_l3:
            logger.debug("WB POWER: L3: %s", power_l3.toString())
            power_total += power_l3.getValue()

        return power_total

    async def get_sun_mode_request(self, value: bool, send_and_receive):
        """Sends a sun mode set request to the storage."""

        request = RscpValue.construct_rscp_value(
            "TAG_WB_REQ_DATA",
            [("TAG_WB_INDEX", self.__index), ("TAG_WB_REQ_SET_SUN_MODE_ACTIVE", value)],
        )
        await send_and_receive(request)

    async def set_max_charge_current_request(self, value: int, send_and_receive):
        """Sends a set max charge current request to the wallbox."""

        request = RscpValue.construct_rscp_value(
            "TAG_WB_REQ_DATA",
            [("TAG_WB_INDEX", self.__index), ("TAG_WB_REQ_SET_MAX_CHARGE_CURRENT", value)],
        )
        await send_and_receive(request)

    async def set_min_charge_current_request(self, value: int, send_and_receive):
        """Sends a set min charge current request to the wallbox."""

        request = RscpValue.construct_rscp_value(
            "TAG_WB_REQ_DATA",
            [("TAG_WB_INDEX", self.__index), ("TAG_WB_REQ_SET_MIN_CHARGE_CURRENT", value)],
        )
        await send_and_receive(request)
