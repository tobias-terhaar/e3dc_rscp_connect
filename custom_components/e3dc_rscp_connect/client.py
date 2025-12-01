"Client which uses RscpConnections to E3DC storage devices."

import logging

from .e3dc.RscpConnection import RscpConnection
from .e3dc.RscpEncryption import RscpEncryption
from .e3dc.RscpFrame import RscpFrame
from .e3dc.RscpValue import RscpValue
from .model.StorageRscpModel import StorageRscpModel
from .model.WallboxRscpModel import WallboxRscpModel

_LOGGER = logging.getLogger(__name__)


class RscpClient:
    "Class which holds an RscpConnection to communicate with an E3DC storage device."

    def __init__(
        self, host: str, port: int, username: str, password: str, rscp_key: str
    ) -> None:
        "Initializes the client connection."
        self.client = RscpConnection(
            host, port, RscpEncryption(rscp_key), username, password
        )
        self.__storage = None
        self.__wallboxes = []

    @property
    def wallboxes(self):
        "Get access to the stored wallbox data."
        return [wallbox.get_model() for wallbox in self.__wallboxes]

    @property
    def storage(self):
        "Get access to storage data."
        return self.__storage.get_model()

    async def _connect_and_login(self) -> None:
        if not self.client.is_connected():
            await self.client.connect()
        if self.client.is_connected() and not self.client.is_authorized():
            if not await self.client.authorize():
                raise ConnectionError(
                    "Couldn't authorize! Check username and password!"
                )

    async def identify_device(self) -> dict:
        "Reads serial number and firmware version from device."
        try:
            if not self.client.is_connected() or not self.client.is_authorized():
                _LOGGER.info("Not connected, try to reconnect!")
                await self._connect_and_login()

            self.__wallboxes.clear()

            requests = []
            requests.extend(StorageRscpModel.get_identification_tags())
            requests.extend(WallboxRscpModel.get_identification_tags())

            received_values = await self.send_and_receive(requests)
            for x in received_values:
                _LOGGER.info(f"received identification: {x.toString()}")
            # TODO read serial number and firmware from wallbox and add data to coordinator *and* to device_info
            #
            for value in received_values:
                storage = StorageRscpModel.identify(value)
                if storage is not None:
                    self.__storage = storage

                wallbox = WallboxRscpModel.identify(value)
                if wallbox is not None:
                    self.__wallboxes.append(wallbox)
                    continue

        except ConnectionError as err:
            raise Exception(f"Error: {err}") from err
        except Exception as err:
            # TODO make Exception more specific
            raise Exception(f"Identification failed! Rscp Key correct?") from err

        return

    async def send_and_receive(self, rscpValuesToSend: list) -> list:
        """Sends and receives data to the device.

        Packs a list of RscpValues into a frame and send it to the device.
        The answer of the device is returned as list of RscpValues.
        """
        await self.client.send(RscpFrame().packFrame(rscpValuesToSend))
        recv_buffer = await self.client.receive()
        recvd_frame_length = RscpFrame.getFrameLength(recv_buffer)

        frame = RscpFrame()
        if len(recv_buffer) > recvd_frame_length:
            frame.unpack(recv_buffer[0:recvd_frame_length])

        return frame.getRscpValues()

    async def send_set_sun_mode_request(self, index: int, value: bool):
        """Sends a sun mode set request to the storage."""

        request = RscpValue.construct_rscp_value(
            "TAG_WB_REQ_DATA",
            [("TAG_WB_INDEX", index), ("TAG_WB_REQ_SET_SUN_MODE_ACTIVE", value)],
        )
        response = await self.send_and_receive(request)
        _LOGGER.debug(f"{response}")

    def __get_value_for_path(self, path, rscp_value: RscpValue):
        "Returns the value for the given path, or None if path not found."
        tag_value = RscpValue.get_tag_by_path([rscp_value], path)
        if tag_value:
            return tag_value.getValue()
        return None

    async def fetch_data(self):
        "Creates RSCP frames and send it to the device, to fetch updated data!"
        result_values = {}
        try:
            if not self.client.is_connected():
                _LOGGER.info("Not connected, try to reconnect!")
                await self._connect_and_login()

            requests = []

            requests.extend(self.__storage.get_rscp_tags())
            self.__create_rscp_tags_for_sgready(requests)

            for wallbox in self.__wallboxes:
                requests.extend(wallbox.get_rscp_tags())
            # transfer data and wait for response
            received_values = await self.send_and_receive(requests)

            for value in received_values:
                if self.__storage.handle_rscp_data(value):
                    continue

                elif value.getTagName() == "TAG_WB_DATA":
                    for wallbox in self.__wallboxes:
                        wallbox.handle_rscp_data(
                            value
                        )  # should check if data has been handled!
                elif value.getTagName() == "TAG_SGR_DATA":
                    result_values.update(self.__extract_sgready_data(value))
                else:
                    _LOGGER.warning("Received unknown tag: %s", value.getTagName())

        except Exception as err:
            # TODO make Exception more specific
            raise Exception("Error during data fetch: {err}") from err

        result_values["storage"] = self.__storage.get_model()
        for wallbox in self.__wallboxes:
            result_values[f"wallbox_{wallbox.index}"] = wallbox.get_model()

        return result_values

    def __create_rscp_tags_for_sgready(self, requests):
        requests.append(
            RscpValue.construct_rscp_value(
                "TAG_SGR_REQ_DATA",
                [("TAG_SGR_INDEX", 0xFF), ("TAG_SGR_REQ_STATE", None)],
            )
        )

    def __extract_sgready_data(self, container: RscpValue):
        extracted_values = {}

        sgr_index = container.get_child("TAG_SGR_INDEX")
        # we need the overall SG Ready state and this is coded inside
        # index = 0xff:
        if sgr_index.getValue() == 0xFF:
            state = container.get_child("TAG_SGR_STATE")
            extracted_values["sg_ready_state"] = (
                state.getValue() if state is not None else None
            )

        return extracted_values

    def __create_rscp_tags_for_sgready(self, requests):
        requests.append(
            RscpValue.construct_rscp_value(
                "TAG_SGR_REQ_DATA",
                [("TAG_SGR_INDEX", 0xFF), ("TAG_SGR_REQ_STATE", None)],
            )
        )
