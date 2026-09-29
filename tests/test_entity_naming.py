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


def _build(cls, mock_entry, key):
    """Builds one entity of every flavour with the same arguments."""
    coordinator = _coordinator()
    if cls in (WallboxPowerSensor, WallboxEnergySensor, WallboxDailyEnergySensor):
        return cls(coordinator, mock_entry, key, 0, lambda: 0)
    if cls is WallboxSessionEnergySensor:
        return cls(coordinator, mock_entry, key, 0, lambda: 0, lambda: "A")
    if cls is PercentageSensor:
        return cls(coordinator, mock_entry, key, lambda: 0)
    return cls(coordinator, mock_entry, key, data_getter=lambda: 0)


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
    """Without this two wallboxes would both carry the same name."""
    entity = _build(cls, mock_entry, "current_power")

    assert entity.has_entity_name is True


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_name_comes_from_the_translations(cls, mock_entry):
    """The entity carries the key, Home Assistant looks up the name."""
    entity = _build(cls, mock_entry, "current_power")

    assert entity.translation_key == "current_power"
    assert getattr(entity, "_attr_name", None) is None


@pytest.mark.parametrize("cls", ALL_SENSORS)
def test_unique_id_follows_the_key(cls, mock_entry):
    """The key is the identity: renaming happens in the translations only."""
    one = _build(cls, mock_entry, "key_one").unique_id
    two = _build(cls, mock_entry, "key_two").unique_id

    assert one != two
    assert "key_one" in one


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
    sensor = _build(WallboxPowerSensor, mock_entry, "current_power")

    info = sensor.device_info
    # "Test Wallbox" already says wallbox, so it is not prefixed again
    assert info["name"] == "Test Wallbox"
    assert "S10-2023-001" not in info["name"]
    assert info["via_device"] == (DOMAIN, "test_entry_id")


def test_storage_device_is_unchanged(mock_entry):
    sensor = _build(PowerSensor, mock_entry, "home_power")

    info = sensor.device_info
    assert info["name"] == "S10-2023-001"
    assert "via_device" not in info
