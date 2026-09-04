"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.select import SelectEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..e3dc_rscp_api import WallboxDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class SunModeSensor(SelectEntity, E3dcConnectEntity):
    """This sensor is used to represent the sun mode of a wallbox."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox_id: int,
        wallbox: WallboxDataModel,
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry, "Wallbox", wallbox_id)
        self._entry = entry
        self.coordinator = coordinator

        self._attr_name = "Lademodus"
        if wallbox.device_name is None:
            wallbox.device_name = "Wallbox unnamed!"

        serial = coordinator.storage.serial.lower().replace("-", "_")
        device_name = wallbox.device_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{device_name}_sun_mode_state"

        self._options = ["Sonnenmodus", "Mischmodus"]
        self._attr_options = self._options

    @property
    def current_option(self) -> str:
        """Get the current selected option."""

        wallbox: WallboxDataModel = self.coordinator.get_wallbox(
            self._sub_device_index or 0
        )
        if wallbox is None:
            return None

        sun_mode = wallbox.sun_mode

        if sun_mode:
            return "Sonnenmodus"
        if sun_mode is None:
            return "Unknown"
        return "Mischmodus"

    async def async_select_option(self, option: str) -> None:
        """Handle the user selecting an option from the UI."""
        if self._sub_device_index is None:
            return

        if option == "Sonnenmodus":
            await self.coordinator.set_sun_mode(self._sub_device_index, True)
        elif option == "Mischmodus":
            await self.coordinator.set_sun_mode(self._sub_device_index, False)

        # refresh data after sending
        await self.coordinator.async_request_refresh()
