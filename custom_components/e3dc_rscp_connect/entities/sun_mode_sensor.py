"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity

from ..coordinator import E3dcRscpCoordinator, WallboxIndentData  # noqa: TID252
from .entity import E3dcConnectEntity


class SunModeSensor(E3dcConnectEntity, SensorEntity):
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
            f"{wallbox_ident.device_name.lower().replace(' ', '_')}_sun_mode_state"
        )

    @property
    def native_value(self):
        "Get the data."
        sun_mode = self.coordinator.data.get(
            f"wb_{self._sub_device_index}_sun_mode_state"
        )

        if sun_mode:
            return "Sonnenmodus"
        return "Mischmodus"
