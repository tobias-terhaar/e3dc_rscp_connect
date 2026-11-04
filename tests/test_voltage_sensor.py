"""Tests for the voltage sensors of the storage (PV strings and phases)."""

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
from homeassistant.const import UnitOfElectricPotential

from e3dc_rscp_connect.e3dc_rscp_api.model.StorageDataModel import PvInverterData
from e3dc_rscp_connect.entities import VoltageSensor
from e3dc_rscp_connect.sensor import (
    get_inverter_mppt_voltage,
    get_inverter_phase_voltage,
)


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator(inverters=None):
    coordinator = Mock()
    coordinator.storage.serial = "S10-123456789012"
    coordinator.storage.inverters = inverters if inverters is not None else {}
    return coordinator


def test_voltage_sensor_attributes(mock_entry):
    sensor = VoltageSensor(
        _coordinator(), mock_entry, "phase_voltage_l1", data_getter=lambda: 230.4
    )

    assert sensor.translation_key == "phase_voltage_l1"
    assert sensor.unique_id == "s10_123456789012_phase_voltage_l1"
    assert sensor.native_unit_of_measurement == UnitOfElectricPotential.VOLT
    assert sensor.device_class == SensorDeviceClass.VOLTAGE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_value == 230.4


def test_is_disabled_by_default(mock_entry):
    sensor = VoltageSensor(
        _coordinator(), mock_entry, "pv_string_1_voltage", data_getter=lambda: None
    )

    assert sensor.entity_registry_enabled_default is False


def test_missing_value_is_none(mock_entry):
    sensor = VoltageSensor(
        _coordinator(), mock_entry, "pv_string_1_voltage", data_getter=lambda: None
    )

    assert sensor.native_value is None


def test_getters_read_the_inverter():
    inverter = PvInverterData(
        voltage_mppt={0: 512.5, 1: 498.0}, voltage_ac={0: 231.2, 2: 230.4}
    )
    coordinator = _coordinator({0: inverter})

    assert get_inverter_mppt_voltage(coordinator, 0, 1) == 498.0
    assert get_inverter_phase_voltage(coordinator, 0, 2) == 230.4
    # not (yet) reported values
    assert get_inverter_mppt_voltage(coordinator, 0, 2) is None
    assert get_inverter_phase_voltage(coordinator, 0, 1) is None


def test_getters_without_inverter_return_none():
    coordinator = _coordinator()

    assert get_inverter_mppt_voltage(coordinator, 0, 0) is None
    assert get_inverter_phase_voltage(coordinator, 0, 0) is None
