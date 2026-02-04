"""Implements the power sensor entity."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfPower

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class WallboxPowerSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to hold power data of E3DC energy storage system."""

    def __init__(
        # TODO: change constructor to get also wallbox data model, like sun_mode_sensor
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        index: int,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, "Wallbox", index)
        self._attr_name = name

        serial = coordinator.storage.serial.lower().replace("-", "_")
        name = name.lower().replace(" ", "_")

        self._attr_unique_id = f"{serial}_{name}_{index}_assigned_power"

        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._index = index

    @property
    def native_value(self):
        """Returns the power value."""
        wallbox = self.coordinator.get_wallbox(self._index)
        if wallbox is None:
            return None

        return wallbox.assigned_power
