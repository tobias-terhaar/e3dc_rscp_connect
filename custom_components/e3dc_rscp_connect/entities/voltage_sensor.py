"""Implements the voltage sensor entity."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricPotential

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class VoltageSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to hold voltage data of E3DC energy storage system."""

    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1
    # voltages are diagnostic values most users do not need, so they are opt-in
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        key: str,
        data_getter,
    ) -> None:
        """Inits the VoltageSensor.

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
        """Returns the voltage value."""
        return self.__data_getter()
