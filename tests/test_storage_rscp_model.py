"""Tests for StorageRscpModel — focused on EMS tag request + response handling."""

import logging
from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.e3dc_rscp_api.model.StorageRscpModel import StorageRscpModel


@pytest.fixture
def storage_model():
    """A StorageRscpModel pre-populated with identification data."""
    return StorageRscpModel(
        serial="S10-123",
        assembly_serial="ASM-1",
        mac_addr="aa:bb:cc:dd:ee:ff",
        sw_version="1.0",
    )


def _tag_names(tags):
    return [t.getTagName() for t in tags]


class TestEmsTagRequests:
    def test_requests_autarky_tag(self, storage_model):
        tags = storage_model.get_rscp_tags()
        assert "TAG_EMS_REQ_AUTARKY" in _tag_names(tags)

    def test_requests_self_consumption_tag(self, storage_model):
        tags = storage_model.get_rscp_tags()
        assert "TAG_EMS_REQ_SELF_CONSUMPTION" in _tag_names(tags)

    def test_existing_power_tags_still_requested(self, storage_model):
        """Adding new tags must not remove any of the existing EMS power requests."""
        tag_names = _tag_names(storage_model.get_rscp_tags())
        for expected in (
            "TAG_EMS_REQ_POWER_HOME",
            "TAG_EMS_REQ_POWER_BAT",
            "TAG_EMS_REQ_POWER_GRID",
            "TAG_EMS_REQ_POWER_PV",
            "TAG_EMS_REQ_BAT_SOC",
            "TAG_EMS_REQ_EMERGENCY_POWER_STATUS",
        ):
            assert expected in tag_names


class TestEmsTagResponses:
    def _make_value(self, tag_name, value):
        v = Mock()
        v.getTagName.return_value = tag_name
        v.getValue.return_value = value
        return v

    def test_autarky_response_sets_model_field(self, storage_model):
        result = storage_model.handle_rscp_data(
            self._make_value("TAG_EMS_AUTARKY", 87.5)
        )

        assert result is True
        assert storage_model.get_model().autarky == 87.5

    def test_self_consumption_response_sets_model_field(self, storage_model):
        result = storage_model.handle_rscp_data(
            self._make_value("TAG_EMS_SELF_CONSUMPTION", 42.0)
        )

        assert result is True
        assert storage_model.get_model().self_consumption == 42.0

    def test_fields_default_to_none(self, storage_model):
        model = storage_model.get_model()
        assert model.autarky is None
        assert model.self_consumption is None

    def test_unknown_ems_tag_returns_false(self, storage_model):
        result = storage_model.handle_rscp_data(
            self._make_value("TAG_EMS_SOMETHING_ELSE", 1)
        )
        assert result is False


class TestAdditionalPower:
    def _make_value(self, tag_name, value):
        v = Mock()
        v.getTagName.return_value = tag_name
        v.getValue.return_value = value
        return v

    def test_negative_device_value_becomes_positive_production(self, storage_model):
        """The EMS reports additional production as negative — the model flips it."""
        result = storage_model.handle_rscp_data(
            self._make_value("TAG_EMS_POWER_ADD", -1500)
        )

        assert result is True
        assert storage_model.get_model().powers.additional == 1500

    def test_zero_stays_zero(self, storage_model):
        storage_model.handle_rscp_data(self._make_value("TAG_EMS_POWER_ADD", 0))

        assert storage_model.get_model().powers.additional == 0

    def test_none_is_kept(self, storage_model):
        storage_model.handle_rscp_data(self._make_value("TAG_EMS_POWER_ADD", None))

        assert storage_model.get_model().powers.additional is None

    def test_pv_power_keeps_its_sign(self, storage_model):
        """Only the additional value is inverted, PV must stay untouched."""
        storage_model.handle_rscp_data(self._make_value("TAG_EMS_POWER_PV", 2400))

        assert storage_model.get_model().powers.pv == 2400


class TestBatteryDataHandling:
    """A storage answers for battery slots that are not equipped (issue #12)."""

    def _bat_container(self, index=None, states=None):
        """Builds a TAG_BAT_DATA container with optional index and device state."""
        children = {}
        if index is not None:
            child = Mock()
            child.getValue.return_value = index
            children["TAG_BAT_INDEX"] = child
        if states is not None:
            children["TAG_BAT_DEVICE_STATE"] = states

        container = Mock()
        container.getTagName.return_value = "TAG_BAT_DATA"
        container.get_child.side_effect = lambda tag: children.get(tag)
        return container

    def _states(self, connected=True, working=True):
        children = {}
        for tag, value in (
            ("TAG_BAT_DEVICE_CONNECTED", connected),
            ("TAG_BAT_DEVICE_WORKING", working),
        ):
            if value is not None:
                child = Mock()
                child.getValue.return_value = value
                children[tag] = child

        states = Mock()
        states.get_child.side_effect = lambda tag: children.get(tag)
        return states

    def test_valid_battery_data_is_stored(self, storage_model):
        result = storage_model.handle_rscp_data(
            self._bat_container(index=0, states=self._states())
        )

        assert result is True
        state = storage_model.get_model().device_states.battery[0]
        assert state.connected is True
        assert state.working is True

    @pytest.mark.parametrize(
        "container_args",
        [
            {},  # no index at all
            {"index": 1},  # index, but no device state
            {"index": 1, "states": "incomplete"},  # device state without children
        ],
    )
    def test_slot_without_data_is_still_claimed(self, storage_model, container_args):
        """Returning False would make the pipeline warn on every poll cycle."""
        if container_args.get("states") == "incomplete":
            container_args["states"] = self._states(connected=None, working=None)

        result = storage_model.handle_rscp_data(self._bat_container(**container_args))

        assert result is True
        assert storage_model.get_model().device_states.battery == {}

    def test_empty_slot_is_reported_only_once(self, storage_model, caplog):
        container = self._bat_container(index=1)

        with caplog.at_level(logging.DEBUG):
            for _ in range(5):
                storage_model.handle_rscp_data(container)

        above_debug = [r for r in caplog.records if r.levelno > logging.DEBUG]
        assert len(above_debug) == 1
        assert "battery 1" in above_debug[0].getMessage()

    def test_other_containers_are_not_claimed(self, storage_model):
        container = Mock()
        container.getTagName.return_value = "TAG_SOMETHING_ELSE"
        container.get_child.return_value = None

        assert storage_model.handle_rscp_data(container) is False
