"This file contains the DataUpdateCoordinator for the e3dc_rscp_connect home assistant integration."

import asyncio
from datetime import UTC, datetime, timedelta
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import RscpClient
from .model.SgReadyDataModel import SgReadyDataModel
from .model.StorageDataModel import StorageDataModel
from .model.WallboxDataModel import WallboxDataModel

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
        self.__device_info_interval = timedelta(minutes=60)

        __update_interval = current.get("update_interval", 10)
        _LOGGER.info("Starting coordinator with update interval: %d", __update_interval)
        super().__init__(
            hass,
            _LOGGER,
            name="E3DC RSCP connect client",
            update_interval=timedelta(seconds=__update_interval),
        )

        self.client = RscpClient(
            self.host, self.port, self.username, self.password, self.key
        )

        self._remote_power_w: int = 0
        self._remote_task: asyncio.Task | None = None

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

    @property
    def sg_ready(self) -> SgReadyDataModel:
        "Get access to the sg ready data."
        return self.client.sg_ready

    def get_wallbox(self, index: int) -> WallboxDataModel:
        "Returns the ident data of a give wallbox."
        return self.client.get_wallbox(index)

    async def _async_update_data(self):
        starttime = time.time()
        data = {}
        try:
            if self.__device_info_need_update():
                await self.__update_device_info()
            data = await self.client.fetch_data()
        except Exception as err:
            _LOGGER.exception("Exception in update_data:")
            raise UpdateFailed(f"Fehler beim Abrufen: {err}") from err
        else:
            duration = time.time() - starttime
            _LOGGER.debug("duration of update_data: %.3f seconds", duration)
            return data

    async def set_sun_mode(self, wallbox_id: int, value: bool):
        "Uses the client implementation to change the sun mode."
        await self.client.send_set_sun_mode_request(wallbox_id, value)

    async def set_max_charge_current(self, wallbox_id: int, value: int):
        "Uses the client implementation to change the max charge current."
        await self.client.send_set_max_charge_current(wallbox_id, value)

    async def set_min_charge_current(self, wallbox_id: int, value: int):
        "Uses the client implementation to change the min charge current."
        await self.client.send_set_min_charge_current(wallbox_id, value)

    @property
    def remote_control_active(self) -> bool:
        "Returns True if the battery remote control loop is running."
        return self._remote_task is not None and not self._remote_task.done()

    def set_battery_remote_setpoint(self, power_w: int) -> None:
        "Updates the power setpoint used by the remote control loop."
        self._remote_power_w = power_w

    async def start_remote_control(self) -> None:
        "Starts the 1-second battery remote control loop."
        if self.remote_control_active:
            return
        self._remote_task = self.hass.loop.create_task(self._remote_control_loop())

    async def stop_remote_control(self) -> None:
        "Stops the remote control loop and resets the battery setpoint to 0 W."
        if self._remote_task is not None and not self._remote_task.done():
            self._remote_task.cancel()
            try:
                await self._remote_task
            except asyncio.CancelledError:
                pass
        self._remote_task = None
        await self.client.disable_remote_control()

    async def _remote_control_loop(self) -> None:
        "Sends the current power setpoint to the battery every second."
        try:
            while True:
                try:
                    await self.client.send_battery_remote_power(self._remote_power_w)
                except Exception:
                    _LOGGER.exception(
                        "Battery remote control: error sending power setpoint"
                    )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
