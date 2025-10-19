"""Implements the charging state sensor for a wallbox."""

from homeassistant.components.sensor import SensorEntity

from ..coordinator import E3dcRscpCoordinator, WallboxIndentData  # noqa: TID252
from .entity import E3dcConnectEntity


class CpStateSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the charging state of a wallbox."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox_id: int,
        wallbox_ident: WallboxIndentData,
    ) -> None:
        "Init the sensor."
        super().__init__(coordinator, entry, "Wallbox", wallbox_id)
        self._entry = entry
        self.coordinator = coordinator

        self._attr_name = "Ladestatus"
        self._attr_unique_id = (
            f"{wallbox_ident.device_name.lower().replace(' ', '_')}_charge_state"
        )

    @property
    def native_value(self):
        "Get the data."
        cp_state = self.coordinator.data.get(f"wb_{self._sub_device_index}_cp_state")

        states = {
            "A": "Cable disconnected",
            "B": "Cable connected",
            "C": "Charging",
            "F": "Error",
        }

        return states.get(cp_state, "Unknown")
