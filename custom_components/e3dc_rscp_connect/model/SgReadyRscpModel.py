"This class contains the SgReadyRscpModel which extracts SG Ready data from a device."

import logging

from rscp_lib.RscpValue import RscpValue
from .RscpModelInterface import RscpModelInterface
from .SgReadyDataModel import SgReadyDataModel


class SgReadyRscpModel(RscpModelInterface):
    """Implementation of SgReadyRscpModel.

    We use the Group Adress 0xFF as index in this implemenation to access the overall SG Ready state!
    """

    def __init__(self):
        self.__model = SgReadyDataModel()

    def __eq__(self, other):
        return isinstance(other, SgReadyRscpModel)

    def __hash__(self):
        return hash(SgReadyRscpModel)

    def get_model(self):
        return self.__model

    @staticmethod
    def get_identification_tags() -> list[RscpValue]:
        """Identification is done, by simply checking if RSCP clients answers on SGR tags."""
        return [
            RscpValue.construct_rscp_value(
                "TAG_SGR_REQ_DATA",
                [("TAG_SGR_INDEX", 0xFF), ("TAG_SGR_REQ_STATE", None)],
            )
        ]

    @staticmethod
    def identify(container: RscpValue) -> RscpModelInterface | None:
        """Identify if rscp client speaks SGR namespace."""

        if container.getTagName() != "TAG_SGR_DATA":
            return None

        sgr_index = container.get_child("TAG_SGR_INDEX")

        if sgr_index.getValue() == 0xFF:
            model = SgReadyRscpModel()
            model.handle_rscp_data(container)
            return model

        return None

    def get_rscp_tags(self) -> list[RscpValue]:
        """Returns all tags used to get informations from device!"""
        return SgReadyRscpModel.get_identification_tags()

    def get_rscp_tags_slow(self) -> list[RscpValue]:
        """This function is equivalent to the get_rscp_tags.

        The slightly different focus is, that the tags returned in this function
        represents slow changing data! The client will use this function only from time
        to time.
        """
        return []

    def handle_rscp_data(self, container: RscpValue) -> bool:
        """This function is used to retrieve data from a rscp tag!"""
        if container.getTagName() != "TAG_SGR_DATA":
            return False

        sgr_index = container.get_child("TAG_SGR_INDEX")
        # we need the overall SG Ready state and this is coded inside
        # index = 0xff:
        if sgr_index.getValue() == 0xFF:
            state = container.get_child("TAG_SGR_STATE")
            self.__model.state = state.getValue() if state is not None else None
            return True
        return False
