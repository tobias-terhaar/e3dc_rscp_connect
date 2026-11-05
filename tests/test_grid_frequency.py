"""Tests for the grid frequency, read from the PV inverter (TAG_PVI_AC_FREQUENCY)."""

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from unittest.mock import Mock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfFrequency
from rscp_lib.RscpValue import RscpValue

from e3dc_rscp_connect.e3dc_rscp_api.model.StorageDataModel import PvInverterData
from e3dc_rscp_connect.e3dc_rscp_api.model.StorageRscpModel import StorageRscpModel
from e3dc_rscp_connect.entities import FrequencySensor
from e3dc_rscp_connect.sensor import get_inverter_frequency


@pytest.fixture
def storage_model():
    return StorageRscpModel(
        serial="S10-123",
        assembly_serial="ASM-1",
        mac_addr="aa:bb:cc:dd:ee:ff",
        sw_version="1.0",
    )


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator(inverters=None):
    coordinator = Mock()
    coordinator.storage.serial = "S10-123456789012"
    coordinator.storage.inverters = inverters if inverters is not None else {}
    return coordinator


def _pvi_data(*children, index=0):
    return RscpValue.construct_rscp_value(
        "TAG_PVI_DATA", [("TAG_PVI_INDEX", index), *children]
    )


class TestReadout:
    def test_frequency_of_phase_0_is_requested(self, storage_model):
        requested = [
            child.getValue()
            for tag in storage_model.get_rscp_tags()
            if tag.getTagName() == "TAG_PVI_REQ_DATA"
            for child in tag.get_childs("TAG_PVI_REQ_AC_FREQUENCY")
        ]

        assert requested
        assert set(requested) == {0}

    def test_frequency_is_stored(self, storage_model):
        result = storage_model.handle_rscp_data(
            _pvi_data(
                ("TAG_PVI_DC_POWER", [("TAG_PVI_INDEX", 0), ("TAG_PVI_VALUE", 1200)]),
                (
                    "TAG_PVI_AC_FREQUENCY",
                    [("TAG_PVI_INDEX", 0), ("TAG_PVI_VALUE", 50.02)],
                ),
            )
        )

        assert result is True
        inverter = storage_model.get_model().inverters[0]
        assert inverter.ac_frequency == 50.02
        assert inverter.power_mppt == {0: 1200}

    def test_answer_without_value_is_none(self, storage_model):
        storage_model.handle_rscp_data(
            _pvi_data(("TAG_PVI_AC_FREQUENCY", [("TAG_PVI_INDEX", 0)]))
        )

        assert storage_model.get_model().inverters[0].ac_frequency is None

    def test_answer_without_frequency_keeps_it_unknown(self, storage_model):
        storage_model.handle_rscp_data(_pvi_data())

        assert storage_model.get_model().inverters[0].ac_frequency is None


def test_sensor_attributes(mock_entry):
    sensor = FrequencySensor(
        _coordinator(), mock_entry, "grid_frequency", data_getter=lambda: 49.98
    )

    assert sensor.translation_key == "grid_frequency"
    assert sensor.unique_id == "s10_123456789012_grid_frequency"
    assert sensor.native_unit_of_measurement == UnitOfFrequency.HERTZ
    assert sensor.device_class == SensorDeviceClass.FREQUENCY
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_value == 49.98


def test_sensor_is_disabled_by_default(mock_entry):
    sensor = FrequencySensor(
        _coordinator(), mock_entry, "grid_frequency", data_getter=lambda: None
    )

    assert sensor.entity_registry_enabled_default is False


def test_getter_reads_the_inverter():
    coordinator = _coordinator({0: PvInverterData(ac_frequency=50.01)})

    assert get_inverter_frequency(coordinator, 0) == 50.01


def test_getter_without_inverter_returns_none():
    assert get_inverter_frequency(_coordinator(), 0) is None
