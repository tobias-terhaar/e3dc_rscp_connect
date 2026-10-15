"""Implements the entity base class."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN  # noqa: TID252
from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..e3dc_rscp_api import WallboxType  # noqa: TID252

# Product names, Home Assistant shows them as the device model.
WALLBOX_MODELS = {
    WallboxType.E3DC: "E3/DC",
    WallboxType.EASY: "Easyconnect",
    WallboxType.EDISON: "Edison",
    WallboxType.MULTI: "Multiconnect",
    WallboxType.EFY: "EFY",
    WallboxType.EDSN: "EDSN",
}


class E3dcConnectEntity(CoordinatorEntity):
    """This entity holds the basic functions of all E3dcConnectEntities."""

    # Home Assistant builds the displayed name as "<device> <entity>" and
    # derives the entity ids the same way. Without this every entity would be
    # named by itself, and two wallboxes would both end up as "Current power".
    _attr_has_entity_name = True

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

    @staticmethod
    def wallbox_device_name(device_name: str | None) -> str:
        """Builds the device name of a wallbox.

        Home Assistant puts the device name in front of every entity name, so
        it has to stay short. The storage it belongs to is expressed through
        via_device instead of being spelled out here. A device name that
        already says "wallbox" is taken as it is, to avoid a stutter like
        "Wallbox Wallbox 1".
        """
        if not device_name:
            return "Wallbox"
        if "wallbox" in device_name.lower():
            return device_name
        return f"Wallbox {device_name}"

    @staticmethod
    def wallbox_model(wallbox_type: WallboxType | int | None) -> str:
        """Builds the device model of a wallbox from its reported type.

        A type the integration does not know yet keeps its number, so it can
        be reported and added.
        """
        if wallbox_type is None:
            return "Wallbox"
        if wallbox_type in WALLBOX_MODELS:
            return WALLBOX_MODELS[wallbox_type]
        return f"(type {int(wallbox_type)})"

    @property
    def device_info(self):
        "Return the device info depending on the subdevice type."
        if self._sub_device_type == "Wallbox":
            wb_info = self.coordinator.get_wallbox(self._sub_device_index)
            return {
                "identifiers": {
                    (DOMAIN, self._entry.entry_id + f"_wb_{self._sub_device_index}")
                },
                "name": self.wallbox_device_name(wb_info.device_name),
                "manufacturer": "E3/DC by HagerEnergy",
                "model": f"Wallbox {self.wallbox_model(wb_info.wallbox_type)}",
                # use sw_version stored in coordinator!
                "sw_version": wb_info.firmware_version,
                # Shows the wallbox below its storage in the device overview,
                # which is what the old "connected to <serial>" name did.
                "via_device": (DOMAIN, self._entry.entry_id),
            }
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self.coordinator.storage.serial,
            "manufacturer": "E3/DC by HagerEnergy",
            "model": "S10",
            "sw_version": self.coordinator.storage.sw_version,
        }
