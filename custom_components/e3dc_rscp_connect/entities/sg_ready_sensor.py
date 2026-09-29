"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class SGReadySensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the sg ready state of the storage system."""

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator

        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_sg_ready_state"

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_translation_key = "sgready_status"
        self._attr_options = [
            "block",
            "normal",
            "go",
            "force_go",
        ]

    @property
    def native_value(self):
        "Get the data."
        sgr = self.coordinator.sg_ready

        if sgr is None:
            return None

        sgr_state = sgr.state

        states = {
            1: "block",
            2: "normal",
            3: "go",
            4: "force_go",
        }

        return states.get(sgr_state)  # returns None if not found!
