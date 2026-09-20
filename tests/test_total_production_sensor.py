"""Tests for the combined production helper used by the Total Production sensors."""

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.e3dc_rscp_api.model.StorageDataModel import EmsPowerModel
from e3dc_rscp_connect.sensor import get_total_production_power


def _coordinator(pv=None, additional=None):
    coordinator = Mock()
    coordinator.storage.powers = EmsPowerModel(pv=pv, additional=additional)
    return coordinator


class TestTotalProductionPower:
    def test_sums_pv_and_additional(self):
        assert get_total_production_power(_coordinator(pv=2400, additional=1500)) == 3900

    def test_without_additional_generators_equals_pv(self):
        assert get_total_production_power(_coordinator(pv=2400, additional=0)) == 2400

    @pytest.mark.parametrize(
        "pv,additional,expected",
        [(2400, None, 2400), (None, 1500, 1500)],
    )
    def test_missing_value_is_treated_as_zero(self, pv, additional, expected):
        assert get_total_production_power(_coordinator(pv, additional)) == expected

    def test_returns_none_before_first_update(self):
        assert get_total_production_power(_coordinator()) is None
