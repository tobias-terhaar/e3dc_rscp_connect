"This file contains WallboxRscpModel. A class to communicate with the wallboxes through RSCP over an storage system."

import logging

from ..e3dc.RscpValue import RscpValue  # noqa: TID252
from .WallboxDataModel import WallboxDataModel

logger = logging.getLogger(__name__)


class WallboxRscpModel:
    "This class represents the RSCP communication with a wallbox and stores the data in a WallboxDataModel."

    def __init__(self, wallbox_index: int) -> None:
        "Inits the WalboxRscpModel for index wallbox_index."
        self.__index = wallbox_index
        self.__model = WallboxDataModel(wallbox_index)

    def get_model(self) -> WallboxDataModel:
        "Returns the data model."
        return self.__model

    @property
    def index(self) -> int:
        return self.__index

    def get_identify_tags(self):
        pass

    def get_rscp_tags(self) -> list:
        "Returns all tags used to get informations from device!"
        return RscpValue.construct_rscp_value(
            "TAG_WB_REQ_DATA",
            [
                ("TAG_WB_INDEX", self.__index),
                ("TAG_WB_REQ_CP_STATE", None),
                ("TAG_WB_REQ_PARAMETER_LIST", 0),
                ("TAG_WB_REQ_PARAMETER_LIST", 1),
                ("TAG_WB_REQ_ACTIVE_CHARGE_STRATEGY", None),
                ("TAG_WB_REQ_ASSIGNED_POWER", None),
                # ("TAG_WB_REQ_POWER", None),
                ("TAG_WB_REQ_DEVICE_STATE", None),
                ("TAG_WB_REQ_SUN_MODE_ACTIVE", None),
                # "TAG_WB_REQ_SET_ABORT_CHARGING"
                # "TAG_WB_REQ_SET_STATION_ENABLED"
                # "TAG_WB_REQ_SET_STATION_AVAILABLE",
            ],
        )

    def get_rscp_tags_slow(self):
        pass

    # def __extract_wallbox_data(self, container: RscpValue):
    def handle_rscp_data(self, container: RscpValue) -> bool:
        "This function is used to retrieve data from a rscp tag!"

        if container.getTagName() != "TAG_WB_DATA":
            return False

        model = WallboxDataModel(self.__index)

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

        value = container.get_child("TAG_WB_CP_STATE")
        logger.debug("CP State: %s", value.toString())
        model.cp_state = value.getValue() if value is not None else None

        assigned_power_container = container.get_child("TAG_WB_ASSIGNED_POWER")
        if assigned_power_container:
            model.assigned_power = sum(
                x.getValue() for x in assigned_power_container.getValue()
            )

        power_container = container.get_child("TAG_WB_POWER")
        if power_container:
            logger.debug("WB POWER: %s", power_container.toString())
            model.power = sum(x.getValue() for x in power_container.getValue())

        value = container.get_child("TAG_WB_SUN_MODE_ACTIVE")
        model.sun_mode = value.getValue() if value is not None else None

        self.__model = model
        return True
