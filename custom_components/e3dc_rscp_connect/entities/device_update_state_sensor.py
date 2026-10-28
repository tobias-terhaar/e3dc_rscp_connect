"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class DeviceUpdateStateSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to make available a device state of the system."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        device: str,
        data_get_func,
        index: int,
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry)
        self._entry = entry
        self.coordinator = coordinator
        serial = coordinator.storage.serial.lower().replace("-", "_")

        self.__data_get_func = data_get_func

        self._attr_translation_key = f"{device.lower()}_update_state"
        self._attr_translation_placeholders = {"index": str(index)}
        self._attr_unique_id = f"{serial}_{device.lower()}{index}_device_update_state"

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["updating", "not_updating"]

    @property
    def native_value(self):
        "Get the data."
        if self.__data_get_func is None:
            return None

        states = self.__data_get_func()

        if states is None:
            return None

        if states.in_service:
            return "updating"
        return "not_updating"
