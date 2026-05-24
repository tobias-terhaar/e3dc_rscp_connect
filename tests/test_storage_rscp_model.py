"""Tests for StorageRscpModel — focused on EMS tag request + response handling."""

from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.model.StorageRscpModel import StorageRscpModel


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
