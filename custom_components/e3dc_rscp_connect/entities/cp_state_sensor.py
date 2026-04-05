"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..model.WallboxDataModel import WallboxDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class CpStateSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the charging state of a wallbox."""

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
        self._index = wallbox_id

        self._attr_name = "Wallbox Status"
        serial = coordinator.storage.serial.lower().replace("-", "_")
        wallbox_name = wallbox.device_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{wallbox_name}_wallbox_state"

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_translation_key = "wallbox_status"
        self._attr_options = [
            "cable_disconnected",
            "cable_connected",
            "charging",
            "error",
        ]

    @property
    def native_value(self):
        "Get the data."
        wallbox: WallboxDataModel = self.coordinator.get_wallbox(self._index)

        if not wallbox:
            return None
        cp_state = wallbox.cp_state

        states = {
            "A": "cable_disconnected",
            "B": "cable_connected",
            "C": "charging",
            "F": "error",
        }

        return states.get(cp_state)
