"This file defines the RscpModelInterface which needs to be implemented by RSCP models to work with the client."

from __future__ import annotations

from abc import ABC, abstractmethod

from ..e3dc.RscpValue import RscpValue  # noqa: TID252


class RscpModelInterface(ABC):
    """This interface needs to be implemented by all classes which want to handle RSCP tags from the client."""

    @staticmethod
    @abstractmethod
    def get_identification_tags() -> list[RscpValue]:
        """Returns a list of tags need to send to identify a device of the implementing class."""

    @staticmethod
    @abstractmethod
    def identify(container: RscpValue) -> RscpModelInterface | None:
        """This function is used to identify a device with the passed data.

        If the identification was successful, the function returns an object
        of the implementing class. If not None is returned.
        """

    @abstractmethod
    def get_rscp_tags(self) -> list[RscpValue]:
        """Returns all tags used to get informations from device!

        The client will call this funciton to get the tags, send them out and passes the
        answer into handle_rscp_data where it is extracted.
        """

    @abstractmethod
    def get_rscp_tags_slow(self) -> list[RscpValue]:
        """This function is equivalent to the get_rscp_tags.

        The slightly different focus is, that the tags returned in this function
        represents slow changing data! The client will use this function only from time
        to time.
        """

    @abstractmethod
    def handle_rscp_data(self, container: RscpValue) -> bool:
        """This function is used to retrieve data from a rscp tag!

        It needs to return True if the data in the container or tag has been
        processed. If the data is not interesting for the implementing class,
        False should be returned.
        """
