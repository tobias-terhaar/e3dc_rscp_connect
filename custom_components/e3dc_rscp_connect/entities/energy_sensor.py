"""Implements the energy sensor entity."""

from datetime import UTC, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.restore_state import RestoreEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class EnergySensor(E3dcConnectEntity, SensorEntity, RestoreEntity):
    """This sensor is used to hold energy data of E3DC energy storage system."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        power_value: str,
        negative_direction: bool = False,
        sub_device_type: str | None = None,
        sub_device_index: str | None = None,
    ) -> None:
        """Inits the PowerSensor with a location. The location is used to create the attribute name and the unique id."""
        super().__init__(coordinator, entry, sub_device_type, sub_device_index)

        self._negative_direction = negative_direction
        self._location = power_value

        self._attr_name = name
        self._attr_unique_id = (
            f"e3dc_rscp_connect_energy_{name.lower().replace(' ', '_')}"
        )
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING

        self._last_update = None
        self._last_power = None
        self._energy_kwh = 0.0

    async def async_added_to_hass(self):
        """Register update callback."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._energy_kwh = float(last_state.state)
            except ValueError:
                self._energy_kwh = 0.0

        self.coordinator.async_add_listener(self._handle_coordinator_update)

    def _handle_coordinator_update(self):
        """Handle updated data from coordinator."""
        now = datetime.now(UTC)
        power_watt = self.coordinator.data.get(f"{self._location}")

        if power_watt is None:
            # _LOGGER.warning("Power value missing for location %s", self._location)
            return

        # check the sign of the power value, count only values for the correct direction!
        if self._negative_direction:
            power_watt = min(power_watt, 0)
            # reverse sign to only create positive counters!
            power_watt *= -1
        else:
            power_watt = max(power_watt, 0)

        if self._last_update is not None:
            # Zeitdifferenz in Stunden
            delta_h = (now - self._last_update).total_seconds() / 3600.0
            avg_power_kw = (self._last_power + power_watt) / 2 / 1000.0
            self._energy_kwh += avg_power_kw * delta_h

            self.async_write_ha_state()

        # Zustand aktualisieren
        self._last_update = now
        self._last_power = power_watt

    @property
    def native_value(self):
        "Returns the native value of the sensor."
        return round(self._energy_kwh, 3)
