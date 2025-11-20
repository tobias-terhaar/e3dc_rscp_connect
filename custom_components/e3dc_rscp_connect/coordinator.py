"This file contains the DataUpdateCoordinator for the e3dc_rscp_connect home assistant integration."

from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import RscpClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class WallboxIndentData:
    "Identity data of a connected wallbox."

    serial: str
    device_name: str
    firmware_version: str
    index: int


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

        self._serialno: str = ""
        self._mac: str = ""
        self._firmware: str = ""

        self._wallbox_count: int = 0
        self._wb_indexes: list = []
        self._wallbox_data: dict = {}

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
        values = await self.client.identify_device()
        self._serialno = values["serial"]
        self._mac = values["mac"]
        self._firmware = values["sw_release"]
        self._wallbox_count = len(values["wb_indexes"])
        self._wb_indexes = values["wb_indexes"]
        self._wallbox_data = {}
        for x in self._wb_indexes:
            serial = values[f"wb_{x}_serial"]
            device_name = values[f"wb_{x}_device_name"]
            firmware_version = values[f"wb_{x}_firmware_version"]
            self._wallbox_data[x] = WallboxIndentData(
                serial, device_name, firmware_version, x
            )

    @property
    def serial(self) -> str:
        return self._serialno

    @property
    def ethernet_mac(self) -> str:
        return self._mac

    @property
    def firmware(self) -> str:
        return self._firmware

    @property
    def wallbox_count(self) -> int:
        "Returns the number of detected wallboxes!"
        return len(self._wb_indexes)

    @property
    def wb_indexes(self) -> list[int]:
        "Returns a list with the wallbox indexes which have been found."
        return self._wb_indexes

    def get_wallbox_ident(self, index: int) -> WallboxIndentData:
        "Returns the ident data of a give wallbox."
        return self._wallbox_data[index]

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
