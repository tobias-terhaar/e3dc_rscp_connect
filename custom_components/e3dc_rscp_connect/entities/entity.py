"""Implements the entity base class."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN  # noqa: TID252
from ..coordinator import E3dcRscpCoordinator  # noqa: TID252


class E3dcConnectEntity(CoordinatorEntity):
    """This entity holds the basic functions of all E3dcConnectEntities."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        sub_device_type: str | None = None,
        sub_device_index: int | None = None,
    ) -> None:
        """Inits the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self.coordinator = coordinator
        self._sub_device_type = sub_device_type
        self._sub_device_index = sub_device_index

    @property
    def device_info(self):
        "Return the device info depending on the subdevice type."
        if self._sub_device_type == "Wallbox":
            wb_info = self.coordinator.get_wallbox_ident(self._sub_device_index)
            return {
                "identifiers": {
                    (DOMAIN, self._entry.entry_id + f"_wb_{self._sub_device_index}")
                },
                "name": f"Wallbox {wb_info.device_name} connected to {self.coordinator.serial}",
                "manufacturer": "E3/DC by HagerEnergy",
                "model": "Wallbox X",
                # use sw_version stored in coordinator!
                "sw_version": wb_info.firmware_version,
            }
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self.coordinator.serial,
            "manufacturer": "E3/DC by HagerEnergy",
            "model": "S10",
            "sw_version": self.coordinator.firmware,
        }
