"Client which uses RscpConnections to E3DC storage devices."

import logging

from .e3dc.RscpConnection import RscpConnection
from .e3dc.RscpEncryption import RscpEncryption
from .e3dc.RscpFrame import RscpFrame
from .e3dc.RscpValue import RscpValue
from .model.RscpHandlerPipeline import RscpHandlerPipeline
from .model.SgReadyRscpModel import SgReadyRscpModel
from .model.StorageRscpModel import StorageRscpModel
from .model.WallboxDataModel import WallboxDataModel
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
        self.__sg_ready = None
        self.__wallboxes = []
        self.__handlerPipeline = RscpHandlerPipeline()

    @property
    def wallboxes(self):
        "Get access to the stored wallbox data."
        return [wallbox.get_model() for wallbox in self.__wallboxes]

    def get_wallbox(self, index: int) -> WallboxDataModel:
        "Returns the ident data of a give wallbox."
        for wallbox in self.wallboxes:
            if wallbox.index == index:
                return wallbox
        return None

    def _get_wallbox(self, index: int) -> WallboxRscpModel:
        "Returns the ident data of a give wallbox."
        for wallbox in self.__wallboxes:
            if wallbox.get_model().index == index:
                return wallbox
        return None

    @property
    def storage(self):
        "Get access to storage data."
        if self.__storage is None:
            return None
        return self.__storage.get_model()

    @property
    def sg_ready(self):
        "Get access to the sg ready data."
        if self.__sg_ready is None:
            return None
        return self.__sg_ready.get_model()

    async def _connect_and_login(self) -> None:
        if not self.client.is_connected():
            await self.client.connect()
        if self.client.is_connected() and not self.client.is_authorized():
            if not await self.client.authorize():
                raise ConnectionError(
                    "Couldn't authorize! Check username and password!"
                )

    def __add_identified_storage(self, storage):
        def set_storage(self, storage):
            _LOGGER.info("Set identified storage: %s!", storage.ident_serial)
            self.__storage = storage
            self.__handlerPipeline.add_handler(storage)

        if storage is None:
            _LOGGER.warning("Can't set storage to None!")
            return

        if self.__storage is None:
            set_storage(self, storage)
            return

        if storage == self.__storage:
            _LOGGER.info("Re-Identified storage: %s!", storage.ident_serial)
        else:
            set_storage(self, storage)

    def __add_identified_sg_ready(self, sg_ready):
        def set_sg_ready(self, sg_ready):
            _LOGGER.info("Set identified sg ready!")
            self.__sg_ready = sg_ready
            self.__handlerPipeline.add_handler(sg_ready)

        if sg_ready is None:
            _LOGGER.warning("Can't set sg_ready to None!")
            return

        if self.__storage is None:
            set_sg_ready(self, sg_ready)
            return

        if sg_ready == self.__sg_ready:
            _LOGGER.info("Re-Identified sg_ready!")
        else:
            set_sg_ready(self, sg_ready)

    def __add_indentified_wallbox(self, wallbox: WallboxRscpModel):
        # sanity checks:
        if wallbox is None:
            return

        if wallbox in self.__wallboxes:
            _LOGGER.info("Re-Identified wallbox: %s", wallbox.serial)
            return

        _LOGGER.info("Identified wallbox: %s", wallbox.serial)
        self.__wallboxes.append(wallbox)
        self.__handlerPipeline.add_handler(wallbox)

    async def identify_device(self) -> dict:
        "Reads serial number and firmware version from device."
        try:
            if not self.client.is_connected() or not self.client.is_authorized():
                _LOGGER.info("Not connected, try to reconnect!")
                await self._connect_and_login()

            # self.__wallboxes.clear()

            requests = []
            requests.extend(StorageRscpModel.get_identification_tags())
            requests.extend(WallboxRscpModel.get_identification_tags())
            requests.extend(SgReadyRscpModel.get_identification_tags())

            received_values = await self.send_and_receive(requests)
            for x in received_values:
                _LOGGER.info("Received identification: %s", x.toString())
            # TODO read serial number and firmware from wallbox and add data to coordinator *and* to device_info
            #
            for value in received_values:
                storage = StorageRscpModel.identify(value)

                if storage is not None:
                    self.__add_identified_storage(storage)
                    continue

                wallbox = WallboxRscpModel.identify(value)
                if wallbox is not None:
                    self.__add_indentified_wallbox(wallbox)
                    continue

                sg_ready = SgReadyRscpModel.identify(value)
                if sg_ready is not None:
                    self.__add_identified_sg_ready(sg_ready)
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

        if recv_buffer is None:
            _LOGGER.warning("Recv buffer is None, decryption failure???")
            return []

        recvd_frame_length = RscpFrame.getFrameLength(recv_buffer)

        frame = RscpFrame()
        if len(recv_buffer) > recvd_frame_length:
            frame.unpack(recv_buffer[0:recvd_frame_length])

        return frame.getRscpValues()

    async def send_set_sun_mode_request(self, index: int, value: bool):
        """Sends a sun mode set request to the storage."""

        wallbox = self._get_wallbox(index)
        if wallbox is not None:
            await wallbox.get_sun_mode_request(value, self.send_and_receive)

    def __get_value_for_path(self, path, rscp_value: RscpValue):
        "Returns the value for the given path, or None if path not found."
        tag_value = RscpValue.get_tag_by_path([rscp_value], path)
        if tag_value:
            return tag_value.getValue()
        return None

    async def _fetch_data(self):
        _LOGGER.debug("Fetch data")
        try:
            if not self.client.is_connected():
                _LOGGER.debug("Not connected, try to reconnect!")
                await self._connect_and_login()

            requests = await self.__handlerPipeline.collect_tags()
            # transfer data and wait for response
            received_values = await self.send_and_receive(requests)
            if received_values is None:
                _LOGGER.warning(
                    "Received no values from device: %s for tags: %s",
                    getattr(self.__storage, "serial", None),
                    requests,
                )

            await self.__handlerPipeline.process(received_values)

        except Exception as err:
            # TODO make Exception more specific
            raise Exception("Error during data fetch: {err}") from err

    async def fetch_data(self):
        "Creates RSCP frames and send it to the device, to fetch updated data!"
        result_values = {}
        _LOGGER.debug("Grab data from fetch_data")
        await self._fetch_data()
        return result_values
