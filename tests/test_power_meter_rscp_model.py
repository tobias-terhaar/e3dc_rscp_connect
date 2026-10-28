"""Tests for PowerMeterRscpModel — identification and the measured values."""

import pytest
from rscp_lib.RscpValue import RscpValue

from e3dc_rscp_connect.e3dc_rscp_api.model.PowerMeterDataModel import (
    PowerMeterDataModel,
    PowerMeterType,
)
from e3dc_rscp_connect.e3dc_rscp_api.model.PowerMeterRscpModel import (
    PowerMeterRscpModel,
)


def _pm_data(index=0, **values):
    """Builds a TAG_PM_DATA container, values adds TAG_PM_<name> children."""
    children = [("TAG_PM_INDEX", index)]
    children.extend((f"TAG_PM_{name.upper()}", value) for name, value in values.items())
    return RscpValue.construct_rscp_value("TAG_PM_DATA", children)


class TestIdentification:
    def test_all_eight_slots_are_requested(self):
        requests = PowerMeterRscpModel.get_identification_tags()

        assert [r.get_child("TAG_PM_INDEX").getValue() for r in requests] == list(
            range(8)
        )
        for request in requests:
            assert request.get_child("TAG_PM_REQ_TYPE") is not None
            assert request.get_child("TAG_PM_REQ_DEVICE_NAME") is not None

    @pytest.mark.parametrize(
        "raw,expected",
        [(1, PowerMeterType.ROOT), (3, PowerMeterType.ADDITIONAL_PRODUCTION)],
    )
    def test_known_type_is_identified(self, raw, expected):
        powermeter = PowerMeterRscpModel.identify(_pm_data(index=2, type=raw))

        assert powermeter.index == 2
        assert powermeter.get_model().pm_type is expected

    @pytest.mark.parametrize("raw", [0, 6])
    def test_slot_without_meter_is_skipped(self, raw):
        """UNDEFINED and UNUSED slots are answered, but have no meter behind them."""
        assert PowerMeterRscpModel.identify(_pm_data(type=raw)) is None

    def test_device_name_is_read(self):
        powermeter = PowerMeterRscpModel.identify(
            _pm_data(type=1, device_name="Hausanschluss")
        )

        assert powermeter.get_model().device_name == "Hausanschluss"

    @pytest.mark.parametrize("values", [{}, {"device_name": ""}])
    def test_missing_device_name_is_none(self, values):
        powermeter = PowerMeterRscpModel.identify(_pm_data(type=1, **values))

        assert powermeter.get_model().device_name is None

    def test_unknown_type_keeps_its_number(self):
        powermeter = PowerMeterRscpModel.identify(_pm_data(type=42))

        assert powermeter.get_model().pm_type == 42

    def test_answer_without_type_is_skipped(self):
        assert PowerMeterRscpModel.identify(_pm_data()) is None

    def test_other_containers_are_ignored(self):
        container = RscpValue.construct_rscp_value(
            "TAG_WB_DATA", [("TAG_WB_INDEX", 0)]
        )

        assert PowerMeterRscpModel.identify(container) is None

    def test_same_slot_is_equal(self):
        assert PowerMeterRscpModel(1, PowerMeterType.ROOT) == PowerMeterRscpModel(1)
        assert PowerMeterRscpModel(1) != PowerMeterRscpModel(2)


class TestDataHandling:
    @pytest.fixture
    def powermeter(self):
        return PowerMeterRscpModel(0, PowerMeterType.ROOT)

    def test_requests_its_own_slot(self, powermeter):
        (request,) = powermeter.get_rscp_tags()

        assert request.getTagName() == "TAG_PM_REQ_DATA"
        assert request.get_child("TAG_PM_INDEX").getValue() == 0

    def test_reads_phases_and_voltages(self, powermeter):
        handled = powermeter.handle_rscp_data(
            _pm_data(
                power_l1=100.0,
                power_l2=-50.0,
                power_l3=25.5,
                voltage_l1=230.1,
                voltage_l2=231.0,
                voltage_l3=229.4,
            )
        )
        model = powermeter.get_model()

        assert handled is True
        assert model.power == pytest.approx(75.5)
        assert model.power_l2 == -50.0
        assert model.voltage_l3 == pytest.approx(229.4)

    def test_data_for_other_index_is_ignored(self, powermeter):
        assert powermeter.handle_rscp_data(_pm_data(index=1, power_l1=1.0)) is False
        assert powermeter.get_model().power is None

    def test_missing_values_are_none(self, powermeter):
        powermeter.handle_rscp_data(_pm_data(power_l1=10.0))
        powermeter.handle_rscp_data(_pm_data())

        assert powermeter.get_model().power is None
        assert powermeter.get_model().voltage_l1 is None

    def test_identification_survives_an_update(self, powermeter):
        powermeter.get_model().device_name = "Hausanschluss"
        powermeter.handle_rscp_data(_pm_data(power_l1=10.0))

        assert powermeter.get_model().pm_type is PowerMeterType.ROOT
        assert powermeter.get_model().device_name == "Hausanschluss"


def test_power_sums_only_the_phases_read():
    model = PowerMeterDataModel(0, power_l1=10.0, power_l3=5.0)

    assert model.power == 15.0
    assert PowerMeterDataModel(0).power is None
