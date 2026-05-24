"""Tests for the generic PercentageSensor entity."""

from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.entities import PercentageSensor


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


@pytest.fixture
def coordinator():
    coord = Mock()
    storage = Mock()
    storage.serial = "S10-123456789012"
    coord.storage = storage
    return coord


def test_returns_value_from_getter(mock_entry, coordinator):
    sensor = PercentageSensor(
        coordinator, mock_entry, "Autarky", data_getter=lambda: 73.2
    )
    assert sensor.native_value == 73.2


def test_returns_none_when_getter_returns_none(mock_entry, coordinator):
    sensor = PercentageSensor(
        coordinator, mock_entry, "Autarky", data_getter=lambda: None
    )
    assert sensor.native_value is None


def test_attributes_for_autarky(mock_entry, coordinator):
    sensor = PercentageSensor(
        coordinator, mock_entry, "Autarky", data_getter=lambda: 50
    )
    assert sensor._attr_name == "Autarky"
    assert sensor._attr_native_unit_of_measurement == "%"
    assert sensor._attr_unique_id == "s10_123456789012_autarky_percentage"


def test_attributes_for_self_consumption(mock_entry, coordinator):
    sensor = PercentageSensor(
        coordinator, mock_entry, "Self Consumption", data_getter=lambda: 50
    )
    assert sensor._attr_name == "Self Consumption"
    assert sensor._attr_unique_id == "s10_123456789012_self_consumption_percentage"


def test_state_class_is_measurement(mock_entry, coordinator):
    sensor = PercentageSensor(
        coordinator, mock_entry, "Autarky", data_getter=lambda: 50
    )
    assert sensor._attr_state_class.value == "measurement"


def test_getter_called_on_each_access(mock_entry, coordinator):
    """Sensor must read fresh data from the coordinator each time HA polls it."""
    values = iter([10, 20, 30])
    sensor = PercentageSensor(
        coordinator, mock_entry, "Autarky", data_getter=lambda: next(values)
    )
    assert sensor.native_value == 10
    assert sensor.native_value == 20
    assert sensor.native_value == 30
