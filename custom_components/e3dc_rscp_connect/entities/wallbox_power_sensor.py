"""Implements the power sensor entity."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
        key: str,
        index,
        data_getter,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id.

        `key` identifies the sensor: it is both its translation key and the
        part of the unique id that names it, so it must not be changed once
        an entity exists. The displayed name comes from the translations.
        """
        super().__init__(coordinator, entry, "Wallbox", index)
        self._attr_translation_key = key
        self.__data_getter = data_getter
        serial = coordinator.storage.serial.lower().replace("-", "_")

        wallbox = coordinator.get_wallbox(index)
        wallbox_name = wallbox.device_name.lower().replace(" ", "_")

        self._attr_unique_id = f"{serial}_{wallbox_name}_{index}_{key}"

        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._index = index

    @property
    def native_value(self):
        """Returns the power value."""

        return self.__data_getter()
