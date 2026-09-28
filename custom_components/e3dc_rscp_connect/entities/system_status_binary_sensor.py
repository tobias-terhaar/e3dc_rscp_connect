"""Implements the binary sensors for the EMS system status register."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class SystemStatusBinarySensor(E3dcConnectEntity, BinarySensorEntity):
    """Represents a single bit of the EMS system status register."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        status_field: str,
    ) -> None:
        "Inits the sensor with the name of the field on the system status model."
        super().__init__(coordinator, entry)

        self._status_field = status_field

        self._attr_name = name
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_{status_field}"

    @property
    def is_on(self):
        "Returns the state of the bit, or None while the register is unknown."
        return getattr(self.coordinator.storage.system_status, self._status_field)
