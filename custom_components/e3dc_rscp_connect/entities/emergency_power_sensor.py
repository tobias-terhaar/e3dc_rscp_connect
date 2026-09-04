"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..e3dc_rscp_api import StorageDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class EmergencyPowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the emergeny power state of the storage system."""

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator
        self._attr_name = "Emergency Power Status"
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_emergency_power_state"

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_translation_key = "ep_status"
        self._attr_options = [
            "not_possible",
            "active",
            "not_active",
            "not_available",
            "island_state",
        ]

    @property
    def native_value(self):
        "Get the data."
        storage: StorageDataModel = self.coordinator.storage
        if storage is None:
            return None

        ep_state = storage.emergency_power_state
        if ep_state is None:
            return None

        states = {
            0: "not_possible",
            1: "active",
            2: "not_active",
            3: "not_available",
            4: "island_state",
        }

        return states.get(ep_state)
