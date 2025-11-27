"""Implements the power sensor entity."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfPower

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class WallboxPowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to hold power data of E3DC energy storage system."""

    def __init__(
        self, coordinator: E3dcRscpCoordinator, entry, name: str, index: int
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, "Wallbox", index)
        self._attr_name = name
        self._attr_unique_id = f"e3dc_rscp_connect_power_assigned_power_{index}"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._index = index

    @property
    def native_value(self):
        """Returns the power value."""
        wallbox = self.coordinator.data.get(f"wallbox_{self._index}")
        return wallbox.assigned_power
