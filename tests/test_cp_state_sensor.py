"This file defines tests for CpStateSensor."

from pathlib import Path
import sys

# Add custom_components to path
custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from e3dc_rscp_connect.entities import CpStateSensor
from e3dc_rscp_connect.model.WallboxDataModel import (
    WallboxDataModel,
)
import pytest


# Mock für WallboxIndentData
class MockWallboxIdent:
    def __init__(self, device_name):
        self.device_name = device_name


# Mock für den Coordinator mit Daten
class MockStorage:
    def __init__(self, serial):
        self.serial = serial


class MockCoordinator:
    def __init__(self, data=None):
        self.data = data or {}
        storage_data = self.data.get("storage", {})
        serial = storage_data.get("serial", "") if isinstance(storage_data, dict) else storage_data.serial
        self.storage = MockStorage(serial)

    def get_wallbox(self, index):
        return self.data.get(f"wallbox_{index}")


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def test_cp_state_sensor_attributes(mock_entry) -> None:
    """Test basic attributes of CpStateSensor."""
    coordinator = MockCoordinator(data={"storage": {"serial": "S10-123456789012"}})
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox=wallbox_ident,
    )

    assert sensor.name == "Wallbox Status"
    assert sensor.unique_id == "s10_123456789012_wallbox_1_wallbox_state"


def test_cp_state_sensor_known_states(mock_entry) -> None:
    """Test cp_state mapping to known states."""
    states = {
        "A": "cable_disconnected",
        "B": "cable_connected",
        "C": "charging",
        "F": "error",
    }

    data_key = "wallbox_1"
    wallbox = WallboxDataModel(1)

    for code, expected_state in states.items():
        wallbox.cp_state = code
        coordinator = MockCoordinator(data={data_key: wallbox, "storage": {"serial": "S10-123456789012"}})
        wallbox_ident = MockWallboxIdent("Wallbox 1")

        sensor = CpStateSensor(
            coordinator=coordinator,
            entry=mock_entry,
            wallbox_id=1,
            wallbox=wallbox_ident,
        )

        assert sensor.native_value == expected_state


def test_cp_state_sensor_unknown_state(mock_entry) -> None:
    """Test cp_state returns 'Unknown' for undefined state."""
    wallbox = WallboxDataModel(1, cp_state="Z")
    coordinator = MockCoordinator(
        data={"wallbox_1": wallbox, "storage": {"serial": "S10-123456789012"}}
    )
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox=wallbox_ident,
    )

    assert sensor.native_value == None


def test_cp_state_sensor_missing_value(mock_entry) -> None:
    """Test behavior when the cp_state key is missing in data."""
    coordinator = MockCoordinator(data={"storage": {"serial": "S10-123456789012"}})
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox=wallbox_ident,
    )

    assert sensor.native_value == None
