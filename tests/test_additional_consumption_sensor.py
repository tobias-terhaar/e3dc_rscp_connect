"""Tests for the helper used by the Additional consumers sensors."""

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from unittest.mock import Mock

from e3dc_rscp_connect.e3dc_rscp_api.model.PowerMeterDataModel import (
    PowerMeterDataModel,
    PowerMeterType,
)
from e3dc_rscp_connect.sensor import get_additional_consumption_power


def _meter(index, pm_type, l1=None, l2=None, l3=None):
    return PowerMeterDataModel(
        index=index, pm_type=pm_type, power_l1=l1, power_l2=l2, power_l3=l3
    )


def _coordinator(*powermeters):
    coordinator = Mock()
    coordinator.powermeters = list(powermeters)
    return coordinator


class TestAdditionalConsumptionPower:
    def test_sums_the_phases_of_one_meter(self):
        meter = _meter(1, PowerMeterType.ADDITIONAL_CONSUMPTION, 30, 25, 25)
        assert get_additional_consumption_power(_coordinator(meter)) == 80

    def test_sums_all_additional_consumption_meters(self):
        heat_pump = _meter(1, PowerMeterType.ADDITIONAL_CONSUMPTION, 1000, 1000, 1000)
        sauna = _meter(2, PowerMeterType.ADDITIONAL_CONSUMPTION, 500, 0, 0)
        assert get_additional_consumption_power(_coordinator(heat_pump, sauna)) == 3500

    def test_ignores_other_meter_roles(self):
        grid = _meter(0, PowerMeterType.ROOT, 2000, 2000, 2000)
        production = _meter(2, PowerMeterType.ADDITIONAL_PRODUCTION, -300, 0, 0)
        heat_pump = _meter(1, PowerMeterType.ADDITIONAL_CONSUMPTION, 100, 0, 0)
        coordinator = _coordinator(grid, production, heat_pump)
        assert get_additional_consumption_power(coordinator) == 100

    def test_raw_type_number_is_accepted(self):
        meter = _meter(1, 4, 50, 0, 0)
        assert get_additional_consumption_power(_coordinator(meter)) == 50

    def test_returns_none_without_such_a_meter(self):
        grid = _meter(0, PowerMeterType.ROOT, 2000, 0, 0)
        assert get_additional_consumption_power(_coordinator(grid)) is None
        assert get_additional_consumption_power(_coordinator()) is None

    def test_returns_none_before_the_first_reading(self):
        meter = _meter(1, PowerMeterType.ADDITIONAL_CONSUMPTION)
        assert get_additional_consumption_power(_coordinator(meter)) is None
