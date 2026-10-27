"""Regression tests for the vendored RSCP transport implementation."""

from pathlib import Path
import sys
from unittest.mock import AsyncMock

import pytest

VENDORED_LIB_PARENT = (
    Path(__file__).parent.parent / "custom_components" / "e3dc_rscp_connect"
)
sys.path.insert(0, str(VENDORED_LIB_PARENT))

from rscp_lib.RscpConnection import RscpConnection
from rscp_lib.RscpEncryption import RscpEncryption
from rscp_lib.RscpFrame import RscpFrame
from rscp_lib.RscpValue import RscpValue


@pytest.mark.asyncio
async def test_receive_reassembles_a_fragmented_encrypted_rscp_frame():
    """A TCP read ending after one cipher block must not truncate the frame."""
    values = [
        RscpValue().withTagName("TAG_EMS_REQ_POWER_PV", None) for _ in range(3)
    ]
    response_plain = RscpFrame().packFrame(values)
    encrypted_response = RscpEncryption("test-key").encrypt(response_plain)
    assert len(encrypted_response) == RscpEncryption.BLOCK_SIZE * 2

    connection = RscpConnection("unused", ciphersuite=RscpEncryption("test-key"))
    connection._receive = AsyncMock(
        side_effect=[
            encrypted_response[: RscpEncryption.BLOCK_SIZE],
            encrypted_response[RscpEncryption.BLOCK_SIZE :],
        ]
    )

    received = await connection.receive()

    assert received[: len(response_plain)] == response_plain
    assert connection._receive.await_count == 2
