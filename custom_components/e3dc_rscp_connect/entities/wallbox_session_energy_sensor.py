"""Implements the charging session energy sensor of a single wallbox."""

from collections.abc import Callable
import logging

from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.util import dt as dt_util

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .wallbox_energy_sensor import WallboxEnergySensor

_LOGGER = logging.getLogger(__name__)

# The CP state of the wallbox tells whether a car is attached: A means no car,
# B means connected and C means charging. F is an error, everything else is
# unknown - neither of them says anything about a session, so they are ignored.
CP_STATE_DISCONNECTED = "A"
CP_STATE_CONNECTED = ("B", "C")


def is_car_connected(cp_state: str | None) -> bool | None:
    """Tells whether a car is attached, or None when the state says nothing."""
    if not cp_state:
        return None

    first = cp_state[0].upper()
    if first == CP_STATE_DISCONNECTED:
        return False
    if first in CP_STATE_CONNECTED:
        return True
    return None


class WallboxSessionEnergySensor(WallboxEnergySensor):
    """Energy charged during the current, or the last, charging session.

    A session starts when the wallbox reports a car as connected or charging
    and ends when it reports that the car is gone again. While a session runs
    the value counts up; when it ends the final value stays until the next
    session starts.

    Disabled by default, the user opts in.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        index: int,
        data_getter: Callable[[], int | None],
        state_getter: Callable[[], str | None],
        key: str | None = None,
    ) -> None:
        "Inits the sensor for the wallbox on the given index."
        super().__init__(coordinator, entry, name, index, data_getter, key)

        self._state_getter = state_getter

        # A counter that restarts with every session is a TOTAL: last_reset
        # names the start of the session the value belongs to.
        self._attr_state_class = SensorStateClass.TOTAL

        self._session_active = False
        self._session_start = None
        # Until the first state is seen there is no transition to detect.
        self._state_seen = False

    @property
    def last_reset(self):
        "Start of the session the current value belongs to."
        return self._session_start

    async def async_added_to_hass(self):
        """Restores the counter together with the session it belongs to."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        last_reset = last_state.attributes.get("last_reset")
        if isinstance(last_reset, str):
            last_reset = dt_util.parse_datetime(last_reset)
        self._session_start = last_reset

    def __start_session(self):
        "Begins a new session, dropping the value of the previous one."
        _LOGGER.debug("Charging session started on wallbox %d", self._index)
        self._session_active = True
        self._session_start = dt_util.now()
        self._energy_kwh = 0.0
        # Drop the reference point as well, so the time the car was away does
        # not end up in the new session.
        self._last_update = None
        self._last_power = None

    def _handle_coordinator_update(self):
        """Tracks the session and only counts while one is running."""
        connected = is_car_connected(self._state_getter())

        if not self._state_seen:
            # First update after a restart: adopt the state as it is instead of
            # reading it as a transition, a session may have been running.
            self._state_seen = True
            self._session_active = connected is True
            if self._session_active and self._session_start is None:
                self._session_start = dt_util.now()
        elif connected is True and not self._session_active:
            self.__start_session()
        elif connected is False and self._session_active:
            # Count the last interval, then close the session.
            super()._handle_coordinator_update()
            _LOGGER.debug(
                "Charging session on wallbox %d ended with %.3f kWh",
                self._index,
                self._energy_kwh,
            )
            self._session_active = False
            return

        if not self._session_active:
            # Between sessions the value of the last one is kept.
            return

        super()._handle_coordinator_update()
