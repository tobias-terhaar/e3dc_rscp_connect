"""Implements the frequency sensor entity."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfFrequency

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class FrequencySensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to hold frequency data of E3DC energy storage system."""

    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3
    # a diagnostic value most users do not need, so it is opt-in
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        key: str,
        data_getter,
    ) -> None:
        """Inits the FrequencySensor.

        `key` identifies the sensor: it is both its translation key and the
        part of the unique id that names it, so it must not be changed once
        an entity exists. The displayed name comes from the translations.
        """
        super().__init__(coordinator, entry)

        self._attr_translation_key = key
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_{key}"
        self.__data_getter = data_getter

    @property
    def native_value(self):
        """Returns the frequency value."""
        return self.__data_getter()
