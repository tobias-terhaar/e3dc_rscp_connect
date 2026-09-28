"""Implements the daily energy sensor entity of a single wallbox."""

from collections.abc import Callable

from homeassistant.components.sensor.const import SensorStateClass
from homeassistant.util import dt as dt_util

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .wallbox_energy_sensor import WallboxEnergySensor


class WallboxDailyEnergySensor(WallboxEnergySensor):
    """Energy charged by a wallbox since midnight, local time.

    The counter starts over at 00:00 in the time zone Home Assistant is
    configured for, so a day here is the day at the installation site
    including its DST shifts, not a UTC day.

    Disabled by default: it duplicates the total counter and is only useful
    for someone who wants a per day figure, so the user opts in.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        index: int,
        data_getter: Callable[[], int | None],
        key: str | None = None,
    ) -> None:
        "Inits the sensor for the wallbox on the given index."
        super().__init__(coordinator, entry, name, index, data_getter, key)

        # A counter that restarts every day is a TOTAL, not a TOTAL_INCREASING:
        # last_reset tells the statistics engine when the drop to 0 is expected
        # instead of letting it guess.
        self._attr_state_class = SensorStateClass.TOTAL

        self._period_start = dt_util.start_of_local_day()

    @property
    def last_reset(self):
        "Midnight of the day the current value belongs to."
        return self._period_start

    async def async_added_to_hass(self):
        """Restores the counter, but only when it is from the current day."""
        await super().async_added_to_hass()

        self._period_start = dt_util.start_of_local_day()

        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        last_reset = last_state.attributes.get("last_reset")
        if isinstance(last_reset, str):
            last_reset = dt_util.parse_datetime(last_reset)

        if last_reset != self._period_start:
            # The restored value belongs to an earlier day.
            self._energy_kwh = 0.0

    def _handle_coordinator_update(self):
        """Starts a new day before the value is integrated any further."""
        start_of_day = dt_util.start_of_local_day()

        if self._period_start != start_of_day:
            self._period_start = start_of_day
            self._energy_kwh = 0.0
            if self._last_update is not None and self._last_update < start_of_day:
                # Only the part of the interval after midnight belongs to the
                # new day, the rest was already counted into the old one.
                self._last_update = start_of_day

        super()._handle_coordinator_update()
