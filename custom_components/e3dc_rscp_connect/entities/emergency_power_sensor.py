"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..model.StorageDataModel import StorageDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class EmergencyPowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the emergeny power state of the storage system."""

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator
        self._attr_name = "Emergency Power Status"
        self._attr_unique_id = "e3dc_rscp_connect_emergency_power_state"

    @property
    def native_value(self):
        "Get the data."
        storage: StorageDataModel = self.coordinator.data.get("storage")
        if storage is None:
            return "Unknown"

        ep_state = storage.emergency_power_state

        states = {
            0: "not possible",
            1: "active",
            2: "not active",
            3: "not available",
            4: "switch in island state",
        }

        return states.get(ep_state, "Unknown")
