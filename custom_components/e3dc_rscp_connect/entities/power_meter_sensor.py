"""Implements the power meter sensor entities."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricPotential, UnitOfPower

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class PowerMeterSensor(E3dcConnectEntity, SensorEntity):
    """Base of the sensors of a power meter, which is a device of its own."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        key: str,
        index: int,
        data_getter,
        enabled_default: bool = True,
    ) -> None:
        """Inits the sensor for the power meter at slot index.

        `key` identifies the sensor: it is both its translation key and the
        part of the unique id that names it, so it must not be changed once
        an entity exists. The displayed name comes from the translations.
        """
        super().__init__(coordinator, entry, "PowerMeter", index)
        self._attr_translation_key = key
        self._attr_entity_registry_enabled_default = enabled_default
        self.__data_getter = data_getter
        serial = coordinator.storage.serial.lower().replace("-", "_")

        self._attr_unique_id = f"{serial}_pm_{index}_{key}"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Returns the value read from the power meter."""
        return self.__data_getter()


class PowerMeterPowerSensor(PowerMeterSensor):
    """Power of a power meter, in total or of one phase."""

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER


class PowerMeterVoltageSensor(PowerMeterSensor):
    """Voltage of one phase of a power meter."""

    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_suggested_display_precision = 1
