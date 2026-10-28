"""Implements the charging state sensor for a wallbox."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorDeviceClass

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from ..e3dc_rscp_api import WallboxDataModel  # noqa: TID252
from .entity import E3dcConnectEntity

_LOGGER = logging.getLogger(__name__)

# The CP state the wallbox reports, mapped onto the states of this sensor.
CP_STATES = {
    "A": "cable_disconnected",
    "A1": "cable_disconnected",
    "B": "cable_connected",
    "B1": "cable_connected",
    "B2": "cable_connected",
    "C": "charging",
    "C1": "charging",
    "C2": "charging",
    "F": "error",
}


class CpStateSensor(E3dcConnectEntity, SensorEntity):
    """This sensor is used to represent the charging state of a wallbox."""

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        wallbox_id: int,
        wallbox: WallboxDataModel,
    ) -> None:
        "Init the sensor."

        super().__init__(coordinator, entry, "Wallbox", wallbox_id)
        self._entry = entry
        self.coordinator = coordinator
        self._index = wallbox_id
        # cp states already warned about, see __report_unexpected
        self.__unexpected_states = set()

        serial = coordinator.storage.serial.lower().replace("-", "_")
        wallbox_name = wallbox.device_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{wallbox_name}_wallbox_state"

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_translation_key = "wallbox_status"
        self._attr_options = [
            "cable_disconnected",
            "cable_connected",
            "charging",
            "error",
        ]

    @property
    def native_value(self):
        "Get the data."
        wallbox: WallboxDataModel = self.coordinator.get_wallbox(self._index)

        if not wallbox:
            return None

        cp_state = wallbox.cp_state
        _LOGGER.debug("CP state of wallbox %s: %s", self._index, cp_state)

        state = CP_STATES.get(cp_state)

        if state is None and cp_state is not None:
            self.__report_unexpected(cp_state)

        return state

    def __report_unexpected(self, cp_state):
        """Warns about a state we cannot map, once per state.

        native_value runs on every poll cycle, so warning every time would
        fill the log with one line per cycle.
        """
        if cp_state in self.__unexpected_states:
            _LOGGER.debug("Unexpected cp state: %s", cp_state)
            return

        self.__unexpected_states.add(cp_state)
        _LOGGER.warning(
            "Unexpected cp state: %s. Further occurrences are logged at debug level.",
            cp_state,
        )
