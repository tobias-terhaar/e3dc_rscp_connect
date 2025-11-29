"""Implements the power sensor entity."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfPower

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class PowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to hold power data of E3DC energy storage system."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        data_getter=None,
        sensor_value_id=None,
        sub_device_type: str | None = None,
        sub_device_index: int | None = None,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, sub_device_type, sub_device_index)

        if data_getter is None and sensor_value_id is None:
            raise ValueError("data_getter or _sensor_value_id must be set!")

        self._attr_name = name
        sensor_id = self._attr_name.lower().replace(" ", "_")
        self._attr_unique_id = f"e3dc_rscp_connect_power_{sensor_id}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self.__data_getter = data_getter
        self._sensor_value_id = sensor_value_id

    @property
    def native_value(self):
        """Returns the power value."""
        if self.__data_getter:
            return self.__data_getter()
        return self.coordinator.data.get(self._sensor_value_id)
