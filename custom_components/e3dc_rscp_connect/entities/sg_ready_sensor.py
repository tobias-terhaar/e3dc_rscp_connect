"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class SGReadySensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the sg ready state of the storage system."""

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator

        self._attr_name = "SG Ready Status"
        self._attr_unique_id = "sg_ready_state"

    @property
    def native_value(self):
        "Get the data."
        sgr_state = self.coordinator.data.get("sg_ready_state")

        states = {
            1: "Block",
            2: "Normal",
            3: "Go",
            4: "Force Go",
        }

        return states.get(sgr_state, "Unknown")
