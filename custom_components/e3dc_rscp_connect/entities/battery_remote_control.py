"""Battery remote control entities: power setpoint (Number) and enable switch (Switch)."""

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import UnitOfPower

from ..coordinator import E3dcRscpCoordinator  # noqa: TID252
from .entity import E3dcConnectEntity


class BatteryRemotePowerNumber(E3dcConnectEntity, NumberEntity):
    """Number entity to set the battery charge/discharge power setpoint.

    Positive values charge the battery, negative values discharge it.
    The value is sent to the device every second while remote control is active.
    """

    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = -10000.0
    _attr_native_max_value = 10000.0
    _attr_native_step = 50.0

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        """Init the entity."""
        super().__init__(coordinator, entry)
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_battery_remote_power"
        self._attr_name = "Batterie Fernsteuerung Leistung"

    @property
    def native_value(self) -> float:
        return float(self.coordinator._remote_power_w)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.set_battery_remote_setpoint(int(value))
        self.async_write_ha_state()


class BatteryRemoteSwitch(E3dcConnectEntity, SwitchEntity):
    """Switch entity that enables/disables the battery remote control loop."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: E3dcRscpCoordinator, entry) -> None:
        """Init the entity."""
        super().__init__(coordinator, entry)
        serial = coordinator.storage.serial.lower().replace("-", "_")
        self._attr_unique_id = f"{serial}_remote_control_active"
        self._attr_name = "Fernsteuerung"

    @property
    def is_on(self) -> bool:
        "Returns the on state."
        return self.coordinator.remote_control_active

    async def async_turn_on(self, **kwargs) -> None:
        "Called when the switch is turned on."
        await self.coordinator.start_remote_control()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        "Called when the switch is turned off."
        await self.coordinator.stop_remote_control()
        self.async_write_ha_state()
