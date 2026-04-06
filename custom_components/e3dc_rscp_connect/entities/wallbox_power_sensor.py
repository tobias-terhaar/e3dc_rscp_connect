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
        index,
        data_getter,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, "Wallbox", index)
        self._attr_name = name
        self.__data_getter = data_getter
        serial = coordinator.storage.serial.lower().replace("-", "_")

        name = name.lower().replace(" ", "_")

        wallbox = coordinator.get_wallbox(index)
        wallbox_name = wallbox.device_name.lower().replace(" ", "_")

        self._attr_unique_id = f"{serial}_{wallbox_name}_{index}_{name}"

        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._index = index

    @property
    def native_value(self):
        """Returns the power value."""

        return self.__data_getter()
