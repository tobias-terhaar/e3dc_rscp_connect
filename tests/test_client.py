"""Tests for RscpClient (client.py)."""

from pathlib import Path
import sys

custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

from unittest.mock import AsyncMock, Mock, call, patch
import pytest

from e3dc_rscp_connect.client import RscpClient
from e3dc_rscp_connect.model.WallboxDataModel import WallboxDataModel
from e3dc_rscp_connect.model.WallboxRscpModel import WallboxRscpModel
from e3dc_rscp_connect.model.StorageRscpModel import StorageRscpModel
from e3dc_rscp_connect.model.SgReadyRscpModel import SgReadyRscpModel


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


def _make_mock_conn():
    conn = Mock()
    conn.is_connected.return_value = False
    conn.is_authorized.return_value = False
    conn.connect = AsyncMock()
    conn.authorize = AsyncMock(return_value=True)
    conn.send = AsyncMock()
    conn.receive = AsyncMock(return_value=None)
    return conn


@pytest.fixture
def mock_conn():
    return _make_mock_conn()


@pytest.fixture
def client(mock_conn):
    with (
        patch("e3dc_rscp_connect.client.RscpConnection", return_value=mock_conn),
        patch("e3dc_rscp_connect.client.RscpEncryption"),
    ):
        return RscpClient("localhost", 5033, "user", "password", "key")


def _make_wallbox_rscp_model(index=1, serial="WB-001"):
    """Create a real WallboxRscpModel for use in tests."""
    wb = WallboxRscpModel(index, serial=serial, device_name="Test WB")
    return wb


# ─────────────────────────────────────────────────────────────────────────────
# Init & basic state
# ─────────────────────────────────────────────────────────────────────────────


class TestInit:
    def test_storage_is_none_initially(self, client):
        assert client.storage is None

    def test_sg_ready_is_none_initially(self, client):
        assert client.sg_ready is None

    def test_wallboxes_is_empty_initially(self, client):
        assert client.wallboxes == []

    def test_connection_object_is_stored(self, client, mock_conn):
        assert client.client is mock_conn


# ─────────────────────────────────────────────────────────────────────────────
# wallboxes property
# ─────────────────────────────────────────────────────────────────────────────


class TestWallboxesProperty:
    def test_returns_empty_list_when_no_wallboxes(self, client):
        assert client.wallboxes == []

    def test_returns_list_of_models(self, client):
        wb_model = WallboxDataModel(1)
        wb = Mock()
        wb.get_model.return_value = wb_model
        client._RscpClient__wallboxes = [wb]

        result = client.wallboxes

        assert result == [wb_model]
        wb.get_model.assert_called_once()

    def test_returns_models_for_multiple_wallboxes(self, client):
        models = [WallboxDataModel(i) for i in range(3)]
        wbs = [Mock() for _ in range(3)]
        for wb, m in zip(wbs, models):
            wb.get_model.return_value = m
        client._RscpClient__wallboxes = wbs

        assert client.wallboxes == models


# ─────────────────────────────────────────────────────────────────────────────
# get_wallbox (public)
# ─────────────────────────────────────────────────────────────────────────────


class TestGetWallbox:
    def test_returns_model_for_correct_index(self, client):
        wb_model = WallboxDataModel(2)
        wb = Mock()
        wb.get_model.return_value = wb_model
        client._RscpClient__wallboxes = [wb]

        assert client.get_wallbox(2) is wb_model

    def test_returns_none_when_not_found(self, client):
        assert client.get_wallbox(99) is None

    def test_returns_none_for_wrong_index(self, client):
        wb_model = WallboxDataModel(1)
        wb = Mock()
        wb.get_model.return_value = wb_model
        client._RscpClient__wallboxes = [wb]

        assert client.get_wallbox(2) is None

    def test_returns_correct_wallbox_from_multiple(self, client):
        models = [WallboxDataModel(i) for i in range(3)]
        wbs = [Mock() for _ in range(3)]
        for wb, m in zip(wbs, models):
            wb.get_model.return_value = m
        client._RscpClient__wallboxes = wbs

        assert client.get_wallbox(1) is models[1]
        assert client.get_wallbox(2) is models[2]


# ─────────────────────────────────────────────────────────────────────────────
# _get_wallbox (private, returns WallboxRscpModel)
# ─────────────────────────────────────────────────────────────────────────────


class TestGetWallboxPrivate:
    def test_returns_rscp_model_for_correct_index(self, client):
        wb = Mock()
        wb.get_model.return_value = WallboxDataModel(3)
        client._RscpClient__wallboxes = [wb]

        assert client._get_wallbox(3) is wb

    def test_returns_none_when_not_found(self, client):
        assert client._get_wallbox(5) is None

    def test_returns_none_for_wrong_index(self, client):
        wb = Mock()
        wb.get_model.return_value = WallboxDataModel(1)
        client._RscpClient__wallboxes = [wb]

        assert client._get_wallbox(2) is None


# ─────────────────────────────────────────────────────────────────────────────
# storage property
# ─────────────────────────────────────────────────────────────────────────────


class TestStorageProperty:
    def test_returns_none_when_storage_not_set(self, client):
        assert client.storage is None

    def test_returns_model_from_storage(self, client):
        model = Mock()
        storage = Mock()
        storage.get_model.return_value = model
        client._RscpClient__storage = storage

        assert client.storage is model
        storage.get_model.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# sg_ready property
# ─────────────────────────────────────────────────────────────────────────────


class TestSgReadyProperty:
    def test_returns_none_when_sg_ready_not_set(self, client):
        assert client.sg_ready is None

    def test_returns_model_from_sg_ready(self, client):
        model = Mock()
        sg = Mock()
        sg.get_model.return_value = model
        client._RscpClient__sg_ready = sg

        assert client.sg_ready is model
        sg.get_model.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# _connect_and_login
# ─────────────────────────────────────────────────────────────────────────────


class TestConnectAndLogin:
    @pytest.mark.asyncio
    async def test_connects_and_authorizes_when_not_connected(self, client, mock_conn):
        mock_conn.is_connected.return_value = False
        mock_conn.is_authorized.return_value = False
        mock_conn.is_connected.side_effect = [False, True]

        await client._connect_and_login()

        mock_conn.connect.assert_called_once()
        mock_conn.authorize.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_connect_when_already_connected(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = False

        await client._connect_and_login()

        mock_conn.connect.assert_not_called()
        mock_conn.authorize.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_nothing_when_connected_and_authorized(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        await client._connect_and_login()

        mock_conn.connect.assert_not_called()
        mock_conn.authorize.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_connection_error_when_authorize_fails(self, client, mock_conn):
        mock_conn.is_connected.side_effect = [False, True]
        mock_conn.is_authorized.return_value = False
        mock_conn.authorize.return_value = False

        with pytest.raises(ConnectionError, match="Couldn't authorize"):
            await client._connect_and_login()


# ─────────────────────────────────────────────────────────────────────────────
# __add_identified_storage (private)
# ─────────────────────────────────────────────────────────────────────────────


class TestAddIdentifiedStorage:
    def test_none_input_does_nothing(self, client):
        client._RscpClient__add_identified_storage(None)
        assert client._RscpClient__storage is None

    def test_sets_storage_on_first_call(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        storage = Mock()
        storage.ident_serial = "S10-001"

        client._RscpClient__add_identified_storage(storage)

        assert client._RscpClient__storage is storage
        pipeline.add_handler.assert_called_once_with(storage)

    def test_replaces_storage_when_different(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline

        old = Mock()
        old.ident_serial = "S10-001"
        new = Mock()
        new.ident_serial = "S10-002"

        # Ensure old != new
        old.__eq__ = lambda self, other: False

        client._RscpClient__storage = old
        client._RscpClient__add_identified_storage(new)

        assert client._RscpClient__storage is new
        pipeline.add_handler.assert_called_once_with(new)

    def test_logs_reidentified_when_same_storage(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        storage = Mock()
        storage.ident_serial = "S10-001"
        storage.__eq__ = lambda self, other: self is other

        client._RscpClient__storage = storage

        client._RscpClient__add_identified_storage(storage)

        # Pipeline must NOT be called again for re-identification
        pipeline.add_handler.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# __add_identified_sg_ready (private)
# ─────────────────────────────────────────────────────────────────────────────


class TestAddIdentifiedSgReady:
    def test_none_input_does_nothing(self, client):
        client._RscpClient__add_identified_sg_ready(None)
        assert client._RscpClient__sg_ready is None

    def test_sets_sg_ready_when_storage_is_none(self, client):
        """When __storage is None (initial state) sg_ready is registered."""
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        sg = Mock()

        client._RscpClient__add_identified_sg_ready(sg)

        assert client._RscpClient__sg_ready is sg
        pipeline.add_handler.assert_called_once_with(sg)

    def test_replaces_sg_ready_when_different(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        # Simulate storage already identified (avoids the __storage is None branch)
        client._RscpClient__storage = Mock()

        old_sg = Mock()
        new_sg = Mock()
        old_sg.__eq__ = lambda self, other: False

        client._RscpClient__sg_ready = old_sg
        client._RscpClient__add_identified_sg_ready(new_sg)

        assert client._RscpClient__sg_ready is new_sg
        pipeline.add_handler.assert_called_once_with(new_sg)

    def test_logs_reidentified_when_same(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        client._RscpClient__storage = Mock()

        sg = Mock()
        sg.__eq__ = lambda self, other: self is other
        client._RscpClient__sg_ready = sg

        client._RscpClient__add_identified_sg_ready(sg)

        pipeline.add_handler.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# __add_indentified_wallbox (private – note the typo in production code)
# ─────────────────────────────────────────────────────────────────────────────


class TestAddIdentifiedWallbox:
    def test_none_input_does_nothing(self, client):
        client._RscpClient__add_indentified_wallbox(None)
        assert client._RscpClient__wallboxes == []

    def test_adds_new_wallbox_to_list(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        wb = _make_wallbox_rscp_model(index=1, serial="WB-001")

        client._RscpClient__add_indentified_wallbox(wb)

        assert wb in client._RscpClient__wallboxes
        pipeline.add_handler.assert_called_once_with(wb)

    def test_does_not_add_duplicate_wallbox(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        wb = _make_wallbox_rscp_model(index=1, serial="WB-001")
        client._RscpClient__wallboxes = [wb]

        client._RscpClient__add_indentified_wallbox(wb)

        assert len(client._RscpClient__wallboxes) == 1
        pipeline.add_handler.assert_not_called()

    def test_adds_multiple_different_wallboxes(self, client):
        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline
        wb1 = _make_wallbox_rscp_model(index=1, serial="WB-001")
        wb2 = _make_wallbox_rscp_model(index=2, serial="WB-002")

        client._RscpClient__add_indentified_wallbox(wb1)
        client._RscpClient__add_indentified_wallbox(wb2)

        assert len(client._RscpClient__wallboxes) == 2
        assert pipeline.add_handler.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# send_and_receive
# ─────────────────────────────────────────────────────────────────────────────


class TestSendAndReceive:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_recv_buffer_is_none(self, client, mock_conn):
        mock_conn.receive.return_value = None
        with patch("e3dc_rscp_connect.client.RscpFrame"):
            result = await client.send_and_receive([])
        assert result == []

    @pytest.mark.asyncio
    async def test_calls_send_with_packed_frame(self, client, mock_conn):
        mock_conn.receive.return_value = None
        with patch("e3dc_rscp_connect.client.RscpFrame") as MockFrame:
            MockFrame.return_value.packFrame.return_value = b"packed_data"
            await client.send_and_receive([Mock()])
        mock_conn.send.assert_called_once_with(b"packed_data")

    @pytest.mark.asyncio
    async def test_unpacks_when_buffer_longer_than_frame(self, client, mock_conn):
        fake_buffer = bytes(20)
        mock_conn.receive.return_value = fake_buffer

        pack_frame = Mock()
        pack_frame.packFrame.return_value = b"packed"
        unpack_frame = Mock()
        unpack_frame.getRscpValues.return_value = ["val1", "val2"]

        with patch("e3dc_rscp_connect.client.RscpFrame") as MockFrame:
            MockFrame.side_effect = [pack_frame, unpack_frame]
            MockFrame.getFrameLength.return_value = 10  # < 20 → unpack is called

            result = await client.send_and_receive([])

        unpack_frame.unpack.assert_called_once_with(fake_buffer[:10])
        assert result == ["val1", "val2"]

    @pytest.mark.asyncio
    async def test_skips_unpack_when_buffer_not_longer_than_frame(self, client, mock_conn):
        fake_buffer = bytes(10)
        mock_conn.receive.return_value = fake_buffer

        pack_frame = Mock()
        pack_frame.packFrame.return_value = b"packed"
        unpack_frame = Mock()
        unpack_frame.getRscpValues.return_value = []

        with patch("e3dc_rscp_connect.client.RscpFrame") as MockFrame:
            MockFrame.side_effect = [pack_frame, unpack_frame]
            MockFrame.getFrameLength.return_value = 10  # == 10, not greater

            await client.send_and_receive([])

        unpack_frame.unpack.assert_not_called()

    @pytest.mark.asyncio
    async def test_serialized_via_lock(self, client, mock_conn):
        """Two concurrent calls should not interleave (lock serializes them)."""
        mock_conn.receive.return_value = None
        call_order = []

        original_send = mock_conn.send

        async def tracking_send(data):
            call_order.append("send")

        async def tracking_receive():
            call_order.append("receive")
            return None

        mock_conn.send = tracking_send
        mock_conn.receive = tracking_receive

        with patch("e3dc_rscp_connect.client.RscpFrame"):
            import asyncio
            await asyncio.gather(
                client.send_and_receive([]),
                client.send_and_receive([]),
            )

        assert call_order == ["send", "receive", "send", "receive"]


# ─────────────────────────────────────────────────────────────────────────────
# send_set_* commands
# ─────────────────────────────────────────────────────────────────────────────


class TestSendSetRequests:
    @pytest.mark.asyncio
    async def test_sun_mode_calls_wallbox(self, client):
        wb = Mock()
        wb.get_model.return_value = WallboxDataModel(1)
        wb.get_sun_mode_request = AsyncMock()
        client._RscpClient__wallboxes = [wb]

        await client.send_set_sun_mode_request(1, True)

        wb.get_sun_mode_request.assert_called_once_with(True, client.send_and_receive)

    @pytest.mark.asyncio
    async def test_sun_mode_does_nothing_when_wallbox_not_found(self, client):
        # Should not raise
        await client.send_set_sun_mode_request(99, True)

    @pytest.mark.asyncio
    async def test_max_charge_current_calls_wallbox(self, client):
        wb = Mock()
        wb.get_model.return_value = WallboxDataModel(1)
        wb.set_max_charge_current_request = AsyncMock()
        client._RscpClient__wallboxes = [wb]

        await client.send_set_max_charge_current(1, 16)

        wb.set_max_charge_current_request.assert_called_once_with(16, client.send_and_receive)

    @pytest.mark.asyncio
    async def test_max_charge_current_does_nothing_when_not_found(self, client):
        await client.send_set_max_charge_current(99, 16)

    @pytest.mark.asyncio
    async def test_min_charge_current_calls_wallbox(self, client):
        wb = Mock()
        wb.get_model.return_value = WallboxDataModel(1)
        wb.set_min_charge_current_request = AsyncMock()
        client._RscpClient__wallboxes = [wb]

        await client.send_set_min_charge_current(1, 6)

        wb.set_min_charge_current_request.assert_called_once_with(6, client.send_and_receive)

    @pytest.mark.asyncio
    async def test_min_charge_current_does_nothing_when_not_found(self, client):
        await client.send_set_min_charge_current(99, 6)


# ─────────────────────────────────────────────────────────────────────────────
# identify_device
# ─────────────────────────────────────────────────────────────────────────────


class TestIdentifyDevice:
    @pytest.mark.asyncio
    async def test_reconnects_when_not_connected(self, client, mock_conn):
        mock_conn.is_authorized.return_value = False
        # _connect_and_login calls is_connected() twice (guard + post-connect auth check),
        # plus the initial check in identify_device → 3 values needed.
        mock_conn.is_connected.side_effect = [False, False, True]

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=[])):
            await client.identify_device()

        mock_conn.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_connect_when_already_connected_and_authorized(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=[])):
            await client.identify_device()

        mock_conn.connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_identifies_and_registers_storage(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        mock_value = Mock()
        mock_value.toString.return_value = "tag"
        mock_storage = Mock(spec=StorageRscpModel)
        mock_storage.ident_serial = "S10-001"

        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline

        with (
            patch.object(client, "send_and_receive", new=AsyncMock(return_value=[mock_value])),
            patch("e3dc_rscp_connect.client.StorageRscpModel.identify", return_value=mock_storage),
        ):
            await client.identify_device()

        assert client._RscpClient__storage is mock_storage
        pipeline.add_handler.assert_called_with(mock_storage)

    @pytest.mark.asyncio
    async def test_identifies_and_registers_wallbox(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        mock_value = Mock()
        mock_value.toString.return_value = "tag"
        mock_wb = Mock(spec=WallboxRscpModel)
        mock_wb.serial = "WB-001"

        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline

        with (
            patch.object(client, "send_and_receive", new=AsyncMock(return_value=[mock_value])),
            patch("e3dc_rscp_connect.client.StorageRscpModel.identify", return_value=None),
            patch("e3dc_rscp_connect.client.WallboxRscpModel.identify", return_value=mock_wb),
        ):
            await client.identify_device()

        assert mock_wb in client._RscpClient__wallboxes
        pipeline.add_handler.assert_called_with(mock_wb)

    @pytest.mark.asyncio
    async def test_identifies_and_registers_sg_ready(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        mock_value = Mock()
        mock_value.toString.return_value = "tag"
        mock_sg = Mock(spec=SgReadyRscpModel)

        pipeline = Mock()
        client._RscpClient__handlerPipeline = pipeline

        with (
            patch.object(client, "send_and_receive", new=AsyncMock(return_value=[mock_value])),
            patch("e3dc_rscp_connect.client.StorageRscpModel.identify", return_value=None),
            patch("e3dc_rscp_connect.client.WallboxRscpModel.identify", return_value=None),
            patch("e3dc_rscp_connect.client.SgReadyRscpModel.identify", return_value=mock_sg),
        ):
            await client.identify_device()

        assert client._RscpClient__sg_ready is mock_sg

    @pytest.mark.asyncio
    async def test_raises_exception_on_connection_error(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        with (
            patch.object(
                client,
                "send_and_receive",
                new=AsyncMock(side_effect=ConnectionError("refused")),
            ),
        ):
            with pytest.raises(Exception):
                await client.identify_device()

    @pytest.mark.asyncio
    async def test_raises_exception_on_generic_error(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        with (
            patch.object(
                client,
                "send_and_receive",
                new=AsyncMock(side_effect=RuntimeError("bad")),
            ),
        ):
            with pytest.raises(Exception, match="Identification failed"):
                await client.identify_device()

    @pytest.mark.asyncio
    async def test_empty_response_registers_nothing(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=[])):
            await client.identify_device()

        assert client._RscpClient__storage is None
        assert client._RscpClient__sg_ready is None
        assert client._RscpClient__wallboxes == []


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_data
# ─────────────────────────────────────────────────────────────────────────────


class TestFetchDataPrivate:
    def _make_pipeline(self, tags=None, values=None):
        pipeline = Mock()
        pipeline.collect_tags = AsyncMock(return_value=tags or [])
        pipeline.process = AsyncMock()
        return pipeline

    @pytest.mark.asyncio
    async def test_reconnects_when_not_connected(self, client, mock_conn):
        # _fetch_data calls is_connected() once, then _connect_and_login calls it twice
        # → 3 values: not connected → not connected (triggers connect()) → connected (skip auth)
        mock_conn.is_connected.side_effect = [False, False, True]
        mock_conn.is_authorized.return_value = False

        pipeline = self._make_pipeline()
        client._RscpClient__handlerPipeline = pipeline

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=[])):
            await client._fetch_data()

        mock_conn.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_processes_received_values(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        received = [Mock(), Mock()]
        pipeline = self._make_pipeline()
        client._RscpClient__handlerPipeline = pipeline

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=received)):
            await client._fetch_data()

        pipeline.process.assert_called_once_with(received)

    @pytest.mark.asyncio
    async def test_skips_process_when_received_is_none(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        pipeline = self._make_pipeline()
        client._RscpClient__handlerPipeline = pipeline

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=None)):
            await client._fetch_data()

        pipeline.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_collects_tags_from_pipeline(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        tags = [Mock(), Mock()]
        pipeline = self._make_pipeline(tags=tags)
        client._RscpClient__handlerPipeline = pipeline

        with patch.object(client, "send_and_receive", new=AsyncMock(return_value=[])) as mock_s_r:
            await client._fetch_data()

        mock_s_r.assert_called_once_with(tags)

    @pytest.mark.asyncio
    async def test_raises_exception_on_error(self, client, mock_conn):
        mock_conn.is_connected.return_value = True
        mock_conn.is_authorized.return_value = True

        pipeline = Mock()
        pipeline.collect_tags = AsyncMock(side_effect=RuntimeError("crash"))
        client._RscpClient__handlerPipeline = pipeline

        with pytest.raises(Exception, match="Error during data fetch"):
            await client._fetch_data()


# ─────────────────────────────────────────────────────────────────────────────
# fetch_data (public)
# ─────────────────────────────────────────────────────────────────────────────


class TestFetchData:
    @pytest.mark.asyncio
    async def test_returns_empty_dict(self, client):
        with patch.object(client, "_fetch_data", new=AsyncMock()):
            result = await client.fetch_data()
        assert result == {}

    @pytest.mark.asyncio
    async def test_calls_private_fetch_data(self, client):
        with patch.object(client, "_fetch_data", new=AsyncMock()) as mock_fetch:
            await client.fetch_data()
        mock_fetch.assert_called_once()
