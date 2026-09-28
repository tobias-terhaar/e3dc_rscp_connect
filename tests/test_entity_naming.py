"""Tests for entity naming: the device context and the unique id decoupling."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.const import DOMAIN
from e3dc_rscp_connect.e3dc_rscp_api import WallboxDataModel
from e3dc_rscp_connect.entities.entity import E3dcConnectEntity
from e3dc_rscp_connect.entities import (
    EnergySensor,
    PercentageSensor,
    PowerSensor,
    WallboxDailyEnergySensor,
    WallboxEnergySensor,
    WallboxPowerSensor,
    WallboxSessionEnergySensor,
)


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def _coordinator():
    wallbox = WallboxDataModel(index=0)
    wallbox.device_name = "Test Wallbox"

    coordinator = Mock()
    coordinator.data = {}
    coordinator.storage.serial = "S10-2023-001"
    coordinator.get_wallbox.return_value = wallbox
    return coordinator


def _build(cls, mock_entry, name, key=None):
    """Builds one entity of every flavour with the same arguments."""
    coordinator = _coordinator()
    if cls in (WallboxPowerSensor,):
        return cls(coordinator, mock_entry, name, 0, lambda: 0, key)
    if cls in (WallboxEnergySensor, WallboxDailyEnergySensor):
        return cls(coordinator, mock_entry, name, 0, lambda: 0, key)
    if cls is WallboxSessionEnergySensor:
        return cls(coordinator, mock_entry, name, 0, lambda: 0, lambda: "A", key)
    if cls is PercentageSensor:
        return cls(coordinator, mock_entry, name, lambda: 0, key=key)
    return cls(coordinator, mock_entry, name, data_getter=lambda: 0, key=key)


ALL_SENSORS = [
    PowerSensor,
    EnergySensor,
    PercentageSensor,
    WallboxPowerSensor,
    WallboxEnergySensor,
    WallboxDailyEnergySensor,
    WallboxSessionEnergySensor,
]


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_entity_name_is_combined_with_the_device(cls, mock_entry):
    """Without this two wallboxes would both be named "Current power"."""
    entity = _build(cls, mock_entry, "Current power", "current_power")

    assert entity.has_entity_name is True
    assert entity.name == "Current power"


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_unique_id_follows_the_key_not_the_name(cls, mock_entry):
    """Renaming an entity must not create a new one."""
    before = _build(cls, mock_entry, "Current power", "current_power").unique_id
    after = _build(cls, mock_entry, "Charging power", "current_power").unique_id

    assert before == after


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_key_defaults_to_the_name(cls, mock_entry):
    """The fallback keeps the ids of entities that pass no key."""
    with_key = _build(cls, mock_entry, "Current power", "current_power").unique_id
    without_key = _build(cls, mock_entry, "Current power").unique_id

    assert with_key == without_key


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_different_keys_give_different_ids(cls, mock_entry):
    one = _build(cls, mock_entry, "Same name", "key_one").unique_id
    two = _build(cls, mock_entry, "Same name", "key_two").unique_id

    assert one != two


# --- Wallbox device name ---------------------------------------------------


@pytest.mark.parametrize(
    "device_name,expected",
    [
        ("Garage", "Wallbox Garage"),
        ("Wallbox 1", "Wallbox 1"),
        ("wallbox links", "wallbox links"),
        ("Easy Connect", "Wallbox Easy Connect"),
        (None, "Wallbox"),
        ("", "Wallbox"),
    ],
)
def test_wallbox_device_name(device_name, expected):
    """The device name is prefixed once, never twice."""
    assert E3dcConnectEntity.wallbox_device_name(device_name) == expected


def test_wallbox_device_info_is_short_and_linked(mock_entry):
    """The serial is no longer part of the name, via_device carries it."""
    sensor = _build(WallboxPowerSensor, mock_entry, "Current power", "current_power")

    info = sensor.device_info
    # "Test Wallbox" already says wallbox, so it is not prefixed again
    assert info["name"] == "Test Wallbox"
    assert "S10-2023-001" not in info["name"]
    assert info["via_device"] == (DOMAIN, "test_entry_id")


def test_storage_device_is_unchanged(mock_entry):
    sensor = _build(PowerSensor, mock_entry, "Home Power", "home_power")

    info = sensor.device_info
    assert info["name"] == "S10-2023-001"
    assert "via_device" not in info
