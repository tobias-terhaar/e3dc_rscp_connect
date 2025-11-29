"This file contains the DataUpdateCoordinator for the e3dc_rscp_connect home assistant integration."

from datetime import UTC, datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import RscpClient
from .model.WallboxDataModel import WallboxDataModel
from .model.StorageDataModel import StorageDataModel

_LOGGER = logging.getLogger(__name__)


class E3dcRscpCoordinator(DataUpdateCoordinator):
    "DataUpdateCoordinator for the e3dc_rscp_connect integration."

    def __init__(self, hass: HomeAssistant, entry) -> None:
        "Initialize the global updater."

        # get configuration data from options or from the initial setup data as fallback
        current = entry.options or entry.data

        self.host = current["host"]
        self.port = current["port"]
        self.username = current["username"]
        self.password = current["password"]
        self.key = current["key"]
        _LOGGER.info(
            "Host: %s, Port: %d, user: %s, password: %s, key: %s",
            self.host,
            self.port,
            self.username,
            self.password,
            self.key,
        )

        self.__last_device_info_update: datetime | None = None
        self.__device_info_interval = timedelta(minutes=5)

        __update_interval = current.get("update_interval", 10)

        super().__init__(
            hass,
            _LOGGER,
            name="E3DC RSCP connect client",
            update_interval=timedelta(seconds=__update_interval),
        )

        self.client = RscpClient(
            self.host, self.port, self.username, self.password, self.key
        )

    def __device_info_need_update(self):
        now = datetime.now(UTC)
        if (
            self.__last_device_info_update is None
            or now - self.__last_device_info_update > self.__device_info_interval
        ):
            self.__last_device_info_update = now
            return True
        return False

    async def __update_device_info(self):
        await self.client.identify_device()

    @property
    def wallboxes(self) -> list[WallboxDataModel]:
        "Returns a list with the wallbox indexes which have been found."
        return self.client.wallboxes

    @property
    def storage(self) -> StorageDataModel:
        "Get access to the storage data."
        return self.client.storage

    def get_wallbox(self, index: int) -> WallboxDataModel:
        "Returns the ident data of a give wallbox."
        for wallbox in self.client.wallboxes:
            if wallbox.index == index:
                return wallbox
        return None

    async def _async_update_data(self):
        try:
            if self.__device_info_need_update():
                await self.__update_device_info()
            return await self.client.fetch_data()
        except Exception as err:
            _LOGGER.exception("Exception in update_data:")
            raise UpdateFailed(f"Fehler beim Abrufen: {err}") from err

    async def set_sun_mode(self, wallbox_id: int, value: bool):
        "Uses the client implementation to change the sun mode."
        await self.client.send_set_sun_mode_request(wallbox_id, value)
