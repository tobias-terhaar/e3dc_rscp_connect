"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.select import SelectEntity

from ..coordinator import E3dcRscpCoordinator, WallboxIndentData  # noqa: TID252
from .entity import E3dcConnectEntity


class SunModeSensor(SelectEntity, E3dcConnectEntity):
    """This sensor is used to represent the sun mode of a wallbox."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox_id: int,
        wallbox_ident: WallboxIndentData,
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry, "Wallbox", wallbox_id)
        self._entry = entry
        self.coordinator = coordinator

        self._attr_name = "Lademodus"
        self._attr_unique_id = (
            f"{wallbox_ident.device_name.lower().replace(' ', '_')}_sun_mode_state1"
        )

        self._options = ["Sonnenmodus", "Mischmodus"]
        self._attr_options = self._options

    @property
    def current_option(self) -> str:
        """Get the current selected option."""
        sun_mode = self.coordinator.data.get(
            f"wb_{self._sub_device_index}_sun_mode_state"
        )
        if sun_mode:
            return "Sonnenmodus"
        return "Mischmodus"

    async def async_select_option(self, option: str) -> None:
        """Handle the user selecting an option from the UI."""
        if option == "Sonnenmodus":
            await self.coordinator.set_sun_mode(self._sub_device_index, True)
        elif option == "Mischmodus":
            await self.coordinator.set_sun_mode(self._sub_device_index, False)

        # refresh data after sending
        await self.coordinator.async_request_refresh()
