"""Tests for the binary sensors exposing the EMS system status register."""

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.binary_sensor import SYSTEM_STATUS_SENSORS
from e3dc_rscp_connect.e3dc_rscp_api.model.StorageDataModel import SystemStatusModel
from e3dc_rscp_connect.entities import SystemStatusBinarySensor


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator(**status):
    coordinator = Mock()
    coordinator.storage.serial = "S10-123456789012"
    coordinator.storage.system_status = SystemStatusModel(**status)
    return coordinator


def test_sensor_attributes(mock_entry):
    sensor = SystemStatusBinarySensor(
        _coordinator(power_derated=True), mock_entry, "Power Derated", "power_derated"
    )

    assert sensor.name == "Power Derated"
    assert sensor.unique_id == "s10_123456789012_power_derated"
    assert sensor.is_on is True


def test_cleared_bit_is_off(mock_entry):
    sensor = SystemStatusBinarySensor(
        _coordinator(power_derated=False), mock_entry, "Power Derated", "power_derated"
    )

    assert sensor.is_on is False


def test_unread_register_stays_unknown(mock_entry):
    """Without an answer from the device the state must not read as "off"."""
    sensor = SystemStatusBinarySensor(
        _coordinator(), mock_entry, "Power Derated", "power_derated"
    )

    assert sensor.is_on is None


@pytest.mark.parametrize("name,status_field", SYSTEM_STATUS_SENSORS)
def test_every_configured_sensor_maps_to_a_model_field(name, status_field, mock_entry):
    sensor = SystemStatusBinarySensor(
        _coordinator(**{status_field: True}), mock_entry, name, status_field
    )

    assert hasattr(SystemStatusModel(), status_field)
    assert sensor.is_on is True


def test_unique_ids_are_distinct(mock_entry):
    coordinator = _coordinator()
    ids = {
        SystemStatusBinarySensor(coordinator, mock_entry, name, field).unique_id
        for name, field in SYSTEM_STATUS_SENSORS
    }

    assert len(ids) == len(SYSTEM_STATUS_SENSORS)
