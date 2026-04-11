"""Number entities for wallbox charge current limits."""

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import EntityCategory, UnitOfElectricCurrent
from homeassistant.core import callback

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..model.WallboxDataModel import WallboxDataModel  # noqa: TID252
from .entity import E3dcConnectEntity


class _WallboxCurrentNumber(E3dcConnectEntity, NumberEntity):
    """Base class for wallbox current number entities with optimistic UI."""

    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_step = 1
    _attr_entity_category = EntityCategory.CONFIG

    _assumed_value: float | None = None

    def _currents(self):
        wallbox: WallboxDataModel = self.coordinator.get_wallbox(self._sub_device_index)
        if wallbox is None:
            return None
        return wallbox.currents

    @property
    def assumed_state(self) -> bool:
        """Return True while waiting for the device to confirm the new value."""
        return self._assumed_value is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """On coordinator update clear the assumed value so the real device value is shown.

        If the device accepted the change the real value matches what was set.
        If not, the real value reverts to what the device actually has.
        """
        self._assumed_value = None
        super()._handle_coordinator_update()


class WallboxMaxCurrentNumber(_WallboxCurrentNumber):
    """Number entity to set the maximum charging current of a wallbox.

    The value is bounded by [lower_limit, upper_limit] from the device.
    """

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox: WallboxDataModel,
    ) -> None:
        """Init the entity."""
        super().__init__(coordinator, entry, "Wallbox", wallbox.index)

        serial = coordinator.storage.serial.lower().replace("-", "_")
        device_name = (wallbox.device_name or "wallbox").lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{device_name}_max_charge_current"
        self._attr_name = "Max Ladestrom"

    @property
    def native_min_value(self) -> float:
        currents = self._currents()
        return float(currents.lower_limit) if currents else 0.0

    @property
    def native_max_value(self) -> float:
        currents = self._currents()
        return float(currents.upper_limit) if currents else 32.0

    @property
    def native_value(self) -> float | None:
        if self._assumed_value is not None:
            return self._assumed_value
        currents = self._currents()
        return float(currents.max) if currents else None

    async def async_set_native_value(self, value: float) -> None:
        """Optimistically update the UI, then send to device and verify."""
        self._assumed_value = value
        self.async_write_ha_state()
        await self.coordinator.set_max_charge_current(self._sub_device_index, int(value))
        await self.coordinator.async_request_refresh()


class WallboxMinCurrentNumber(_WallboxCurrentNumber):
    """Number entity to set the minimum charging current of a wallbox.

    The value is bounded by [lower_limit, currents.max] from the device.
    """

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox: WallboxDataModel,
    ) -> None:
        """Init the entity."""
        super().__init__(coordinator, entry, "Wallbox", wallbox.index)

        serial = coordinator.storage.serial.lower().replace("-", "_")
        device_name = (wallbox.device_name or "wallbox").lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{device_name}_min_charge_current"
        self._attr_name = "Min Ladestrom"

    @property
    def native_min_value(self) -> float:
        currents = self._currents()
        return float(currents.lower_limit) if currents else 0.0

    @property
    def native_max_value(self) -> float:
        currents = self._currents()
        return float(currents.max) if currents else 32.0

    @property
    def native_value(self) -> float | None:
        if self._assumed_value is not None:
            return self._assumed_value
        currents = self._currents()
        return float(currents.min) if currents else None

    async def async_set_native_value(self, value: float) -> None:
        """Optimistically update the UI, then send to device and verify."""
        self._assumed_value = value
        self.async_write_ha_state()
        await self.coordinator.set_min_charge_current(self._sub_device_index, int(value))
        await self.coordinator.async_request_refresh()
