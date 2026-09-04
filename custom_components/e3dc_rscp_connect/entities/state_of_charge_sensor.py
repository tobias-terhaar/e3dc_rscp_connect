"""Implements the battery state of charge sensor."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..e3dc_rscp_api import StorageDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class StateOfChargeSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the battery charge level."""

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)

        self._attr_name = "Ladezustand"
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_soc"

        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY

    @property
    def native_value(self):
        "Get the data."
        storage: StorageDataModel = self.coordinator.storage
        if storage is None:
            return "Unknown"

        return storage.bat_soc
