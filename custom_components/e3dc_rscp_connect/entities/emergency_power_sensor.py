"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class EmergencyPowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the emergeny power state of the storage system."""

    def __init__(
        self, coordinator: E3dcRscpCoordinator, entry, sensor_value_id
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator
        self._attr_name = "Emergency Power Status"
        self._sensor_value_id = sensor_value_id
        self._attr_unique_id = f"e3dc_rscp_connect_ep_{sensor_value_id}"

    @property
    def native_value(self):
        "Get the data."
        ep_state = self.coordinator.data.get(self._sensor_value_id)

        states = {
            0: "not possible",
            1: "active",
            2: "not active",
            3: "not available",
            4: "switch in island state",
        }

        return states.get(ep_state, "Unknown")
