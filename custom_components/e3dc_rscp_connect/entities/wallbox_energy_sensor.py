"""Implements the energy sensor entity of a single wallbox."""

from collections.abc import Callable

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .energy_sensor import EnergySensor


class WallboxEnergySensor(EnergySensor):
    """Energy counter of a single wallbox, integrated from its power value.

    Home Assistant's energy dashboard only accepts energy entities (kWh,
    device class energy, state class total increasing) as an individual
    device, so the power value of a wallbox alone cannot be used there.
    """

    def __init__(
        self,
        coordinator: E3dcRscpCoordinator,
        entry,
        name: str,
        index: int,
        data_getter: Callable[[], int | None],
        key: str | None = None,
    ) -> None:
        """Inits the sensor for the wallbox on the given index.

        `key` identifies the sensor in its unique id. It defaults to the name,
        so pass it explicitly to keep the id stable across a rename.
        """
        super().__init__(
            coordinator,
            entry,
            name,
            data_getter=data_getter,
            sub_device_type="Wallbox",
            sub_device_index=index,
        )

        # The unique id has to carry the wallbox, otherwise the sensors of two
        # wallboxes would collide. Same scheme as the WallboxPowerSensor.
        serial = coordinator.storage.serial.lower().replace("-", "_")
        wallbox_name = coordinator.get_wallbox(index).device_name.lower().replace(
            " ", "_"
        )
        sensor_name = key or name.lower().replace(" ", "_")
        self._attr_unique_id = f"{serial}_{wallbox_name}_{index}_{sensor_name}_energy"

        self._index = index
