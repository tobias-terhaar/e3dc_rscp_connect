"This file contains StorageRscpModel. A class to communicate with a E3DC storage system."

import logging

from ..e3dc.RscpValue import RscpValue  # noqa: TID252
from .RscpModelInterface import RscpModelInterface
from .StorageDataModel import PvInverterData, StorageDataModel

logger = logging.getLogger(__name__)


class StorageRscpModel(RscpModelInterface):
    """The implemetation of the class to communicate with a storage system."""

    def __init__(
        self,
        serial: str | None = None,
        assembly_serial: str | None = None,
        mac_addr: str | None = None,
        sw_version: str | None = None,
    ) -> None:
        "Inits the StorageRscpModel."
        self.__model = StorageDataModel(
            serial=serial,
            assembly_serial=assembly_serial,
            mac_addr=mac_addr,
            sw_version=sw_version,
        )
        self.__pvi_identified = False

    def get_model(self):
        "Returns the model data."
        return self.__model

    # this are helper class variables for identification, because the identifcation is not done in a container,
    # but with independent tags.
    ident_serial: str | None = None
    ident_assembly_serial: str | None = None
    ident_mac_addr: str | None = None
    ident_sw_version: str | None = None

    @staticmethod
    def get_identification_tags() -> list[RscpValue]:
        """Returns a list of tags need to send to identify a device of the implementing class."""
        # clear identification storage
        StorageRscpModel.ident_serial = None
        StorageRscpModel.ident_assembly_serial = None
        StorageRscpModel.ident_mac_addr = None
        StorageRscpModel.ident_sw_version = None

        requests = []
        requests.append(RscpValue().withTagName("TAG_INFO_REQ_SERIAL_NUMBER", None))
        requests.append(RscpValue().withTagName("TAG_INFO_REQ_MAC_ADDRESS", None))
        requests.append(RscpValue().withTagName("TAG_INFO_REQ_SW_RELEASE", None))
        requests.append(
            RscpValue().withTagName("TAG_INFO_REQ_ASSEMBLY_SERIAL_NUMBER", None)
        )

        return requests

    @staticmethod
    def identify(container: RscpValue) -> RscpModelInterface | None:
        """This function is used to identify a device with the passed data.

        If the identification was successful, the function returns an object
        of the implementing class. If not None is returned.
        """
        if container.getTagName() == "TAG_INFO_SERIAL_NUMBER":
            StorageRscpModel.ident_serial = container.getValue()

        elif container.getTagName() == "TAG_INFO_ASSEMBLY_SERIAL_NUMBER":
            StorageRscpModel.ident_assembly_serial = container.getValue()

        elif container.getTagName() == "TAG_INFO_MAC_ADDRESS":
            StorageRscpModel.ident_mac_addr = container.getValue()

        elif container.getTagName() == "TAG_INFO_SW_RELEASE":
            StorageRscpModel.ident_sw_version = container.getValue()
        else:
            return None

        if (
            StorageRscpModel.ident_serial is not None
            and StorageRscpModel.ident_assembly_serial is not None
            and StorageRscpModel.ident_mac_addr is not None
            and StorageRscpModel.ident_sw_version is not None
        ):
            logger.info("Storage %s identified!", StorageRscpModel.ident_serial)
            return StorageRscpModel(
                StorageRscpModel.ident_serial,
                StorageRscpModel.ident_assembly_serial,
                StorageRscpModel.ident_mac_addr,
                StorageRscpModel.ident_sw_version,
            )
        return None

    def __get_ident_tags_for_pvi(self):
        _list = []
        for index in range(7):
            _list.extend(self.__create_rscp_tags_for_inverter(index))
        return _list

    def get_rscp_tags(self) -> list[RscpValue]:
        """Returns all tags used to get informations from device!

        The client will call this funciton to get the tags, send them out and passes the
        answer into handle_rscp_data where it is extracted.
        """
        tags = []

        tags.extend(self.__create_rscp_tags_for_ems())
        if not self.__pvi_identified:
            tags.extend(self.__get_ident_tags_for_pvi())
            self.__pvi_identified = True
        else:
            for x in self.__model.inverters:
                tags.extend(self.__create_rscp_tags_for_inverter(x))
        return tags

    def get_rscp_tags_slow(self) -> list[RscpValue]:
        """This function is equivalent to the get_rscp_tags.

        The slightly different focus is, that the tags returned in this function
        represents slow changing data! The client will use this function only from time
        to time.
        """

    def handle_rscp_data(self, container: RscpValue) -> bool:
        """This function is used to retrieve data from a rscp tag!

        It needs to return True if the data in the container or tag has been
        processed. If the data is not interesting for the implementing class,
        False should be returned.
        """
        if container.getTagName().startswith("TAG_EMS_"):
            return self.__handle_rcsp_tags_for_ems(container)
        if container.getTagName() == "TAG_PVI_DATA":
            return self.__hanlde_rscp_tags_for_pvi(container)
        return False

    def __create_rscp_tags_for_ems(self):
        requests = []
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_HOME", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_BAT", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_GRID", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_PV", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_ADD", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_WB_ALL", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_POWER_WB_SOLAR", None))
        requests.append(RscpValue().withTagName("TAG_EMS_REQ_BAT_SOC", None))
        requests.append(
            RscpValue().withTagName("TAG_EMS_REQ_EMERGENCY_POWER_STATUS", None)
        )
        return requests

    def __handle_rcsp_tags_for_ems(self, value: RscpValue):
        if value.getTagName() == "TAG_EMS_BAT_SOC":
            self.__model.bat_soc = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_HOME":
            self.__model.powers.home = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_BAT":
            self.__model.powers.battery = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_GRID":
            self.__model.powers.grid = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_PV":
            self.__model.powers.pv = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_ADD":
            self.__model.powers.additional = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_WB_ALL":
            self.__model.powers.wallbox = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_POWER_WB_SOLAR":
            self.__model.powers.wallbox_pv = value.getValue()
            return True
        if value.getTagName() == "TAG_EMS_EMERGENCY_POWER_STATUS":
            self.__model.emergency_power_state = value.getValue()
            return True

        return False
        # else:
        #    _LOGGER.warning("Received unknown EMS tag: %s", value.getTagName())

    def __create_rscp_tags_for_inverter(self, index: int) -> list[RscpValue]:
        return [
            RscpValue.construct_rscp_value(
                "TAG_PVI_REQ_DATA",
                [
                    ("TAG_PVI_INDEX", index),
                    # ("TAG_PVI_REQ_AC_POWER", 0),
                    # ("TAG_PVI_REQ_AC_POWER", 1),
                    # ("TAG_PVI_REQ_AC_POWER", 2),
                    # ("TAG_PVI_REQ_AC_VOLTAGE", 0),
                    # ("TAG_PVI_REQ_AC_VOLTAGE", 1),
                    # ("TAG_PVI_REQ_AC_VOLTAGE", 2),
                    ("TAG_PVI_REQ_DC_POWER", 0),
                    ("TAG_PVI_REQ_DC_POWER", 1),
                    ("TAG_PVI_REQ_DC_POWER", 2),
                ],
            )
        ]

    def __hanlde_rscp_tags_for_pvi(self, container: RscpValue) -> bool:
        pvi_index = container.get_child("TAG_PVI_INDEX")
        if pvi_index is None:
            # check if we ever run into this area!!

            value = container.get_child("TAG_PVI_REQ_INDEX")
            if value is not None:
                logger.critical(
                    "No TAG_PVI_REQ_INDEX in container, errorcode: %d", value.getValue()
                )
            return False

        pvi_index = pvi_index.getValue()

        error = container.get_child("TAG_PVI_REQ_DATA")
        if error is not None:
            logger.warning(
                "No data for inverter: %d, errorcode: %d",
                pvi_index,
                error.getValue(),
            )
            # even if we detected an error, means we handled this tag ;)
            return True

        # get corresponding inverter model
        inverter = self.__model.inverters.get(pvi_index, None)

        if inverter is None:
            inverter = PvInverterData()
            self.__model.inverters[pvi_index] = inverter
            logger.warning("Added inverter on index %d to storage", pvi_index)

        dc_power_tags = container.get_childs("TAG_PVI_DC_POWER")
        for tag in dc_power_tags:
            mppt_index = tag.get_child("TAG_PVI_INDEX")
            if mppt_index is not None:
                mppt_index = mppt_index.getValue()
                power_value = tag.get_child("TAG_PVI_VALUE")
                inverter.power_mppt[mppt_index] = (
                    power_value.getValue() if power_value is not None else None
                )

        return True
