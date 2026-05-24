"""Implements a generic percentage sensor entity."""

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class PercentageSensor(E3dcConnectEntity, SensorEntity):
    """Sensor for values reported as a percentage (autarky, self-consumption, ...)."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        data_getter,
        sub_device_type: str | None = None,
        sub_device_index: int | None = None,
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry, sub_device_type, sub_device_index)

        self._attr_name = name
        slug = name.lower().replace(" ", "_")
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_{slug}_percentage"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self.__data_getter = data_getter

    @property
    def native_value(self):
        "Get the data."
        return self.__data_getter()
