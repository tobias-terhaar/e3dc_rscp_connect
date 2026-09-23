"""Tests for RscpHandlerPipeline — focused on how unhandled tags are logged."""

import logging

from unittest.mock import Mock

import pytest

from e3dc_rscp_connect.e3dc_rscp_api.model.RscpHandlerPipeline import (
    RscpHandlerPipeline,
)


def _value(tag_name):
    value = Mock()
    value.getTagName.return_value = tag_name
    return value


def _handler(handles: bool):
    handler = Mock()
    handler.handle_rscp_data.return_value = handles
    return handler


@pytest.mark.asyncio
async def test_unhandled_tag_warns_once_then_debug(caplog):
    """A tag that stays unhandled must not warn on every poll cycle."""
    pipeline = RscpHandlerPipeline()
    pipeline.add_handler(_handler(False))

    with caplog.at_level(logging.DEBUG):
        for _ in range(5):
            await pipeline.process([_value("TAG_BAT_DATA")])

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    debugs = [r for r in caplog.records if r.levelno == logging.DEBUG]

    assert len(warnings) == 1
    assert "TAG_BAT_DATA" in warnings[0].getMessage()
    assert len(debugs) == 4


@pytest.mark.asyncio
async def test_every_unhandled_tag_is_reported_once(caplog):
    pipeline = RscpHandlerPipeline()
    pipeline.add_handler(_handler(False))

    with caplog.at_level(logging.WARNING):
        await pipeline.process([_value("TAG_BAT_DATA"), _value("TAG_PVI_DATA")])
        await pipeline.process([_value("TAG_BAT_DATA"), _value("TAG_PVI_DATA")])

    messages = [r.getMessage() for r in caplog.records]
    assert sum("TAG_BAT_DATA" in m for m in messages) == 1
    assert sum("TAG_PVI_DATA" in m for m in messages) == 1


@pytest.mark.asyncio
async def test_handled_tag_is_not_reported(caplog):
    pipeline = RscpHandlerPipeline()
    pipeline.add_handler(_handler(True))

    with caplog.at_level(logging.DEBUG):
        await pipeline.process([_value("TAG_BAT_DATA")])

    assert caplog.records == []
