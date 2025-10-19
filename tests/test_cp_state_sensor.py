"This file defines tests for CpStateSensor"

from config.custom_components.e3dc_rscp_connect.entities import CpStateSensor
import pytest


# Mock für WallboxIndentData
class MockWallboxIdent:
    def __init__(self, device_name):
        self.device_name = device_name


# Mock für den Coordinator mit Daten
class MockCoordinator:
    def __init__(self, data=None):
        self.data = data or {}


@pytest.fixture
def mock_entry():
    return type("MockEntry", (), {"entry_id": "test_entry_id"})


def test_cp_state_sensor_attributes(mock_entry) -> None:
    """Test basic attributes of CpStateSensor."""
    coordinator = MockCoordinator()
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox_ident=wallbox_ident,
    )

    assert sensor.name == "Ladestatus"
    assert sensor.unique_id == "wallbox_1_charge_state"


def test_cp_state_sensor_known_states(mock_entry) -> None:
    """Test cp_state mapping to known states."""
    states = {
        "A": "Cable disconnected",
        "B": "Cable connected",
        "C": "Charging",
        "F": "Error",
    }

    for code, expected_state in states.items():
        data_key = "wb_1_cp_state"
        coordinator = MockCoordinator(data={data_key: code})
        wallbox_ident = MockWallboxIdent("Wallbox 1")

        sensor = CpStateSensor(
            coordinator=coordinator,
            entry=mock_entry,
            wallbox_id=1,
            wallbox_ident=wallbox_ident,
        )

        assert sensor.native_value == expected_state


def test_cp_state_sensor_unknown_state(mock_entry) -> None:
    """Test cp_state returns 'Unknown' for undefined state."""
    coordinator = MockCoordinator(data={"wb_1_cp_state": "Z"})
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox_ident=wallbox_ident,
    )

    assert sensor.native_value == "Unknown"


def test_cp_state_sensor_missing_value(mock_entry) -> None:
    """Test behavior when the cp_state key is missing in data."""
    coordinator = MockCoordinator(data={})
    wallbox_ident = MockWallboxIdent("Wallbox 1")

    sensor = CpStateSensor(
        coordinator=coordinator,
        entry=mock_entry,
        wallbox_id=1,
        wallbox_ident=wallbox_ident,
    )

    assert sensor.native_value == "Unknown"
