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
        sensor_value_id: str,
        sub_device_type: str | None = None,
        sub_device_index: int | None = None,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, sub_device_type, sub_device_index)
        self._attr_name = name
        self._sensor_value_id = sensor_value_id
        self._attr_unique_id = f"e3dc_rscp_connect_power_{sensor_value_id}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER

    @property
    def native_value(self):
        """Returns the power value."""
        return self.coordinator.data.get(self._sensor_value_id)
