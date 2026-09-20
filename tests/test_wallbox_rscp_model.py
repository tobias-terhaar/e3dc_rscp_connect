"""Tests for WallboxRscpModel — focused on the power-meter data handling."""

import pytest
from rscp_lib.RscpValue import RscpValue

from e3dc_rscp_connect.e3dc_rscp_api.model.WallboxRscpModel import WallboxRscpModel


@pytest.fixture
def wallbox_model():
    """A WallboxRscpModel for wallbox index 0."""
    return WallboxRscpModel(0, serial="WB-123", device_name="Test WB")


def _wb_data(index=0, **power):
    """Builds a TAG_WB_DATA container with the given power-meter phase values."""
    children = [("TAG_WB_INDEX", index)]
    children.extend(
        (f"TAG_WB_PM_POWER_{phase.upper()}", value) for phase, value in power.items()
    )
    return RscpValue.construct_rscp_value("TAG_WB_DATA", children)


class TestWallboxPowerHandling:
    def test_sums_all_three_phases(self, wallbox_model):
        result = wallbox_model.handle_rscp_data(_wb_data(l1=100.0, l2=200.0, l3=400.0))

        assert result is True
        assert wallbox_model.get_model().power == 700.0

    def test_l2_is_counted_once_and_not_as_l3(self, wallbox_model):
        """Regression: L2 used to read the L3 tag, so L3 was counted twice."""
        wallbox_model.handle_rscp_data(_wb_data(l1=0.0, l2=200.0, l3=400.0))

        assert wallbox_model.get_model().power == 600.0

    def test_missing_phases_are_skipped(self, wallbox_model):
        wallbox_model.handle_rscp_data(_wb_data(l1=250.0))

        assert wallbox_model.get_model().power == 250.0

    def test_data_for_other_index_is_ignored(self, wallbox_model):
        result = wallbox_model.handle_rscp_data(_wb_data(index=1, l1=999.0))

        assert result is False
