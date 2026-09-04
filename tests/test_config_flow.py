"""Tests for the config and options flow (config_flow.py)."""

import sys
from pathlib import Path

custom_components_path = (
    Path(__file__).parent.parent.parent.parent / "config" / "custom_components"
)
sys.path.insert(0, str(custom_components_path))

import asyncio
from unittest.mock import Mock

import pytest
import voluptuous as vol
from e3dc_rscp_connect.config_flow import (
    E3DCRscpConnectConfigFlow,
    OptionsFlowHandler,
    credentials_errors,
    credentials_schema,
    entry_data,
    parse_rscp_port,
)
from e3dc_rscp_connect.const import (
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    LOCAL_USERNAME,
    LOGIN_TYPE_LOCAL,
    LOGIN_TYPE_PORTAL,
)

DEVICE_DESCRIPTION = """<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion><major>1</major><minor>0</minor></specVersion>
  <device>
    <friendlyName>S10-742210004447</friendlyName>
    <UDN>S10-742210004447</UDN>
    <deviceType>urn:schemas-upnp-org:device:HVAC_System:1</deviceType>
    <manufacturer>E3DC</manufacturer>
    <serialNumber>S10-742210004447</serialNumber>
    <serviceList>
      <service name="RSCP_SERVICE_PROVIDER">
        <ENCRYPTION>AES</ENCRYPTION>
        <INTERFACE>ETH</INTERFACE>
        <PORT>5033</PORT>
        <PROTOCOL>TCP</PROTOCOL>
      </service>
      <service name="IModBusService">
        <INTERFACE>ETH</INTERFACE>
        <PORT>502</PORT>
        <PROTOCOL>TCP</PROTOCOL>
      </service>
    </serviceList>
  </device>
</root>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def run(coro):
    """Run a flow step without depending on an async test plugin."""
    return asyncio.run(coro)


def schema_keys(schema):
    """Field names of a voluptuous schema, in order."""
    return [str(key) for key in schema.schema]


def schema_defaults(schema):
    """Mapping of field name to default value, for fields that have one."""
    return {
        str(key): key.default()
        for key in schema.schema
        if key.default is not vol.UNDEFINED
    }


class StubOptionsFlow(OptionsFlowHandler):
    """Options flow with a stubbed config entry.

    ``config_entry`` is a read-only property on ``OptionsFlow``.
    """

    def __init__(self, current: dict) -> None:
        super().__init__()
        self._entry = Mock(options=current, data=current)

    @property
    def config_entry(self):
        return self._entry


LOCAL_ENTRY = {
    "host": "192.168.0.10",
    "port": 5033,
    "username": LOCAL_USERNAME,
    "password": "pw",
    "key": "k",
    "update_interval": 15,
    "login_type": LOGIN_TYPE_LOCAL,
}

PORTAL_ENTRY = {
    "host": "192.168.0.10",
    "port": 5033,
    "username": "me@example.com",
    "password": "pw",
    "key": "k",
    "update_interval": 15,
    "login_type": LOGIN_TYPE_PORTAL,
}

LOCAL_INPUT = {
    "login_type": LOGIN_TYPE_LOCAL,
    "host": "192.168.0.10",
    "port": 5033,
    "password": "pw",
    "key": "k",
}

PORTAL_INPUT = {
    "login_type": LOGIN_TYPE_PORTAL,
    "host": "192.168.0.10",
    "port": 5033,
    "username": "me@example.com",
    "password": "pw",
    "key": "k",
}


@pytest.fixture
def flow():
    return E3DCRscpConnectConfigFlow()


@pytest.fixture
def discovered_flow():
    flow = E3DCRscpConnectConfigFlow()
    flow._discovered_host = "192.168.0.10"
    flow._discovered_name = "S10-742210004447"
    flow._discovered_port = 5034
    return flow


# ─────────────────────────────────────────────────────────────────────────────
# Device description parsing
# ─────────────────────────────────────────────────────────────────────────────


def test_parse_rscp_port_returns_rscp_service_port():
    assert parse_rscp_port(DEVICE_DESCRIPTION) == 5033


def test_parse_rscp_port_ignores_other_services():
    xml = DEVICE_DESCRIPTION.replace('name="RSCP_SERVICE_PROVIDER"', 'name="Other"')
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_handles_custom_port():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "<PORT>5034</PORT>")
    assert parse_rscp_port(xml) == 5034


def test_parse_rscp_port_without_namespace():
    xml = DEVICE_DESCRIPTION.replace(' xmlns="urn:schemas-upnp-org:device-1-0"', "")
    assert parse_rscp_port(xml) == 5033


def test_parse_rscp_port_with_missing_port_element():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "")
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_with_non_numeric_port():
    xml = DEVICE_DESCRIPTION.replace("<PORT>5033</PORT>", "<PORT>abc</PORT>")
    assert parse_rscp_port(xml) is None


def test_parse_rscp_port_with_invalid_xml():
    assert parse_rscp_port("not xml at all <<<") is None


def test_parse_rscp_port_with_empty_document():
    assert parse_rscp_port("") is None


# ─────────────────────────────────────────────────────────────────────────────
# Schema building
# ─────────────────────────────────────────────────────────────────────────────


def test_manual_schema_starts_with_the_login_type():
    schema = credentials_schema(include_host=True, include_port=True)
    assert schema_keys(schema) == [
        "login_type",
        "host",
        "port",
        "username",
        "password",
        "key",
    ]


def test_discovery_schema_has_no_host_and_port_field():
    schema = credentials_schema(include_host=False, include_port=False)
    assert schema_keys(schema) == ["login_type", "username", "password", "key"]


def test_schema_can_ask_for_the_port_without_the_host():
    schema = credentials_schema(include_host=False, include_port=True)
    assert schema_keys(schema) == ["login_type", "port", "username", "password", "key"]


def test_options_schema_has_update_interval():
    schema = credentials_schema(
        include_host=True, include_port=True, include_update_interval=True
    )
    assert schema_keys(schema) == [
        "login_type",
        "host",
        "port",
        "username",
        "password",
        "key",
        "update_interval",
    ]


def test_schema_accepts_input_without_a_username():
    """The username is optional, a local login does not need one."""
    schema = credentials_schema(include_host=False, include_port=False)
    validated = schema({"login_type": LOGIN_TYPE_LOCAL, "password": "pw", "key": "k"})
    assert "username" not in validated


def test_schema_defaults_fall_back_to_constants():
    schema = credentials_schema(
        include_host=True, include_port=True, include_update_interval=True
    )
    defaults = schema_defaults(schema)
    assert defaults["login_type"] == LOGIN_TYPE_LOCAL
    assert defaults["port"] == DEFAULT_PORT
    assert defaults["update_interval"] == DEFAULT_UPDATE_INTERVAL
    assert "host" not in defaults
    assert "username" not in defaults


def test_schema_uses_given_defaults():
    schema = credentials_schema(
        include_host=True,
        include_port=True,
        defaults={
            "login_type": LOGIN_TYPE_PORTAL,
            "host": "192.168.0.10",
            "port": 5034,
            "username": "me@example.com",
        },
    )
    defaults = schema_defaults(schema)
    assert defaults["login_type"] == LOGIN_TYPE_PORTAL
    assert defaults["host"] == "192.168.0.10"
    assert defaults["port"] == 5034
    assert defaults["username"] == "me@example.com"


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────


def test_portal_login_without_username_is_rejected():
    assert credentials_errors(
        {"login_type": LOGIN_TYPE_PORTAL, "password": "pw", "key": "k"}
    ) == {"username": "username_required"}


def test_portal_login_with_blank_username_is_rejected():
    assert credentials_errors(
        {"login_type": LOGIN_TYPE_PORTAL, "username": "   ", "password": "pw"}
    ) == {"username": "username_required"}


def test_portal_login_with_username_is_accepted():
    assert credentials_errors(PORTAL_INPUT) == {}


def test_local_login_without_username_is_accepted():
    assert credentials_errors(LOCAL_INPUT) == {}


# ─────────────────────────────────────────────────────────────────────────────
# Entry data
# ─────────────────────────────────────────────────────────────────────────────


def test_entry_data_fixes_username_for_local_login():
    data = entry_data(LOCAL_INPUT)
    assert data["username"] == LOCAL_USERNAME
    assert data["login_type"] == LOGIN_TYPE_LOCAL


def test_entry_data_ignores_a_username_typed_for_a_local_login():
    """The username field stays on the form, a local login must not use it."""
    data = entry_data({**LOCAL_INPUT, "username": "me@example.com"})
    assert data["username"] == LOCAL_USERNAME


def test_entry_data_keeps_username_for_portal_login():
    data = entry_data(PORTAL_INPUT)
    assert data["username"] == "me@example.com"
    assert data["login_type"] == LOGIN_TYPE_PORTAL


def test_entry_data_strips_the_portal_username():
    data = entry_data({**PORTAL_INPUT, "username": "  me@example.com  "})
    assert data["username"] == "me@example.com"


def test_entry_data_does_not_mutate_user_input():
    user_input = dict(LOCAL_INPUT)
    entry_data(user_input)
    assert "username" not in user_input


# ─────────────────────────────────────────────────────────────────────────────
# Manual config flow
# ─────────────────────────────────────────────────────────────────────────────


def test_user_step_shows_one_form_with_the_login_type(flow):
    result = run(flow.async_step_user())
    assert result["step_id"] == "user"
    assert "login_type" in schema_keys(result["data_schema"])
    assert result["errors"] == {}


def test_user_step_creates_entry_with_local_user(flow):
    flow.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(flow.async_step_user(LOCAL_INPUT))

    assert result["title"] == "192.168.0.10"
    assert result["data"]["username"] == LOCAL_USERNAME
    assert result["data"]["login_type"] == LOGIN_TYPE_LOCAL


def test_user_step_creates_entry_with_portal_user(flow):
    flow.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(flow.async_step_user(PORTAL_INPUT))

    assert result["data"]["username"] == "me@example.com"
    assert result["data"]["login_type"] == LOGIN_TYPE_PORTAL


def test_user_step_reports_a_missing_portal_username(flow):
    user_input = {**PORTAL_INPUT}
    del user_input["username"]

    result = run(flow.async_step_user(user_input))

    assert result["step_id"] == "user"
    assert result["errors"] == {"username": "username_required"}
    # The already entered values are kept, only the username is missing.
    defaults = schema_defaults(result["data_schema"])
    assert defaults["login_type"] == LOGIN_TYPE_PORTAL
    assert defaults["host"] == "192.168.0.10"


# ─────────────────────────────────────────────────────────────────────────────
# Discovery
# ─────────────────────────────────────────────────────────────────────────────


def test_discovery_form_omits_host_and_port(discovered_flow):
    """Host and port come from the discovery, everything else is asked for."""
    result = run(discovered_flow.async_step_discovery_confirm())
    assert result["step_id"] == "discovery_confirm"
    assert schema_keys(result["data_schema"]) == [
        "login_type",
        "username",
        "password",
        "key",
    ]
    assert result["description_placeholders"]["host"] == "192.168.0.10"
    assert result["description_placeholders"]["port"] == "5034"


def test_discovery_form_can_always_change_the_login_type(discovered_flow):
    """Resuming an interrupted discovery must not lock in the login type."""
    first = run(discovered_flow.async_step_discovery_confirm())
    resumed = run(discovered_flow.async_step_discovery_confirm())

    assert schema_keys(first["data_schema"]) == schema_keys(resumed["data_schema"])
    assert schema_defaults(resumed["data_schema"])["login_type"] == LOGIN_TYPE_LOCAL


def test_discovery_creates_entry_with_local_user(discovered_flow):
    discovered_flow.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(
        discovered_flow.async_step_discovery_confirm(
            {"login_type": LOGIN_TYPE_LOCAL, "password": "pw", "key": "k"}
        )
    )

    assert result["title"] == "S10-742210004447"
    assert result["data"]["host"] == "192.168.0.10"
    assert result["data"]["port"] == 5034
    assert result["data"]["username"] == LOCAL_USERNAME
    assert result["data"]["login_type"] == LOGIN_TYPE_LOCAL


def test_discovery_creates_entry_with_portal_user(discovered_flow):
    discovered_flow.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(
        discovered_flow.async_step_discovery_confirm(
            {
                "login_type": LOGIN_TYPE_PORTAL,
                "username": "me@example.com",
                "password": "pw",
                "key": "k",
            }
        )
    )

    assert result["data"]["host"] == "192.168.0.10"
    assert result["data"]["port"] == 5034
    assert result["data"]["username"] == "me@example.com"
    assert result["data"]["login_type"] == LOGIN_TYPE_PORTAL


def test_discovery_reports_a_missing_portal_username(discovered_flow):
    result = run(
        discovered_flow.async_step_discovery_confirm(
            {"login_type": LOGIN_TYPE_PORTAL, "password": "pw", "key": "k"}
        )
    )

    assert result["step_id"] == "discovery_confirm"
    assert result["errors"] == {"username": "username_required"}
    assert result["description_placeholders"]["name"] == "S10-742210004447"


# ─────────────────────────────────────────────────────────────────────────────
# Options flow
# ─────────────────────────────────────────────────────────────────────────────


def test_options_form_prefills_a_local_entry():
    result = run(StubOptionsFlow(LOCAL_ENTRY).async_step_init())

    assert result["step_id"] == "init"
    defaults = schema_defaults(result["data_schema"])
    assert defaults["login_type"] == LOGIN_TYPE_LOCAL
    assert defaults["host"] == "192.168.0.10"
    assert defaults["update_interval"] == 15
    # The fixed local user is never suggested as a portal username.
    assert "username" not in defaults


def test_options_form_prefills_a_portal_entry():
    result = run(StubOptionsFlow(PORTAL_ENTRY).async_step_init())

    defaults = schema_defaults(result["data_schema"])
    assert defaults["login_type"] == LOGIN_TYPE_PORTAL
    assert defaults["username"] == "me@example.com"


def test_options_form_infers_the_login_type_of_older_entries():
    """Entries created before the login type was stored have no login_type."""
    legacy_local = {k: v for k, v in LOCAL_ENTRY.items() if k != "login_type"}
    legacy_portal = {k: v for k, v in PORTAL_ENTRY.items() if k != "login_type"}

    local = run(StubOptionsFlow(legacy_local).async_step_init())
    portal = run(StubOptionsFlow(legacy_portal).async_step_init())

    assert schema_defaults(local["data_schema"])["login_type"] == LOGIN_TYPE_LOCAL
    assert schema_defaults(portal["data_schema"])["login_type"] == LOGIN_TYPE_PORTAL


def test_options_switch_to_local_stores_local_user():
    handler = StubOptionsFlow(PORTAL_ENTRY)
    handler.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(handler.async_step_init({**LOCAL_INPUT, "update_interval": 20}))

    assert result["data"]["username"] == LOCAL_USERNAME
    assert result["data"]["login_type"] == LOGIN_TYPE_LOCAL
    assert result["data"]["update_interval"] == 20


def test_options_switch_to_portal_stores_given_user():
    handler = StubOptionsFlow(LOCAL_ENTRY)
    handler.async_create_entry = Mock(side_effect=lambda **kwargs: kwargs)

    result = run(handler.async_step_init({**PORTAL_INPUT, "update_interval": 20}))

    assert result["data"]["username"] == "me@example.com"
    assert result["data"]["login_type"] == LOGIN_TYPE_PORTAL


def test_options_reports_a_missing_portal_username():
    handler = StubOptionsFlow(LOCAL_ENTRY)
    user_input = {**PORTAL_INPUT, "update_interval": 20}
    del user_input["username"]

    result = run(handler.async_step_init(user_input))

    assert result["step_id"] == "init"
    assert result["errors"] == {"username": "username_required"}


# ─────────────────────────────────────────────────────────────────────────────
# Reauth
# ─────────────────────────────────────────────────────────────────────────────


def _reauth_flow(data: dict, options: dict | None = None):
    """A config flow in the reauth state for an entry with the given config."""
    flow = E3DCRscpConnectConfigFlow()
    flow.context = {"title_placeholders": {"name": "S10-742210004447"}}
    entry = Mock(data=data, options=options or {}, title="S10-742210004447")
    flow._get_reauth_entry = Mock(return_value=entry)
    flow.async_update_reload_and_abort = Mock(side_effect=lambda entry, **kw: kw)
    return flow, entry


def test_reauth_asks_for_credentials_only():
    flow, _ = _reauth_flow(PORTAL_ENTRY)

    result = run(flow.async_step_reauth({}))

    assert result["step_id"] == "reauth_confirm"
    assert schema_keys(result["data_schema"]) == [
        "login_type",
        "username",
        "password",
        "key",
    ]
    assert result["description_placeholders"]["host"] == "192.168.0.10"


def test_reauth_provides_every_placeholder_of_the_flow_title():
    """Home Assistant only fills in the name, flow_title also needs the host."""
    flow, _ = _reauth_flow(PORTAL_ENTRY)

    run(flow.async_step_reauth(PORTAL_ENTRY))

    placeholders = flow.context["title_placeholders"]
    assert placeholders == {"name": "S10-742210004447", "host": "192.168.0.10"}


def test_reauth_takes_the_title_host_from_the_options():
    """The options win over the data, the title has to follow."""
    options = {**PORTAL_ENTRY, "host": "192.168.0.20"}
    flow, _ = _reauth_flow(PORTAL_ENTRY, options=options)

    run(flow.async_step_reauth(PORTAL_ENTRY))

    assert flow.context["title_placeholders"]["host"] == "192.168.0.20"


def test_reauth_form_does_not_prefill_the_rejected_secrets():
    """Password and key were rejected, so they must be entered again."""
    flow, _ = _reauth_flow(PORTAL_ENTRY)

    result = run(flow.async_step_reauth_confirm())

    defaults = schema_defaults(result["data_schema"])
    assert defaults["login_type"] == LOGIN_TYPE_PORTAL
    assert defaults["username"] == "me@example.com"
    assert "password" not in defaults
    assert "key" not in defaults


def test_reauth_updates_the_entry_data():
    flow, _ = _reauth_flow(PORTAL_ENTRY)

    result = run(
        flow.async_step_reauth_confirm(
            {
                "login_type": LOGIN_TYPE_PORTAL,
                "username": "me@example.com",
                "password": "new-pw",
                "key": "new-key",
            }
        )
    )

    assert result["data"]["password"] == "new-pw"
    assert result["data"]["key"] == "new-key"
    # Host and port are not part of the form and must survive.
    assert result["data"]["host"] == "192.168.0.10"
    assert result["data"]["port"] == 5033


def test_reauth_also_updates_the_options_when_they_are_in_use():
    """The coordinator prefers the options, so stale ones would win."""
    stale_options = {**PORTAL_ENTRY, "password": "old-pw", "key": "old-key"}
    flow, _ = _reauth_flow(PORTAL_ENTRY, options=stale_options)

    result = run(
        flow.async_step_reauth_confirm(
            {
                "login_type": LOGIN_TYPE_PORTAL,
                "username": "me@example.com",
                "password": "new-pw",
                "key": "new-key",
            }
        )
    )

    assert result["options"]["password"] == "new-pw"
    assert result["options"]["key"] == "new-key"
    assert result["options"]["update_interval"] == 15


def test_reauth_can_switch_to_the_local_user():
    flow, _ = _reauth_flow(PORTAL_ENTRY)

    result = run(
        flow.async_step_reauth_confirm(
            {"login_type": LOGIN_TYPE_LOCAL, "password": "new-pw", "key": "new-key"}
        )
    )

    assert result["data"]["username"] == LOCAL_USERNAME
    assert result["data"]["login_type"] == LOGIN_TYPE_LOCAL


def test_reauth_reports_a_missing_portal_username():
    flow, _ = _reauth_flow(LOCAL_ENTRY)

    result = run(
        flow.async_step_reauth_confirm(
            {"login_type": LOGIN_TYPE_PORTAL, "password": "pw", "key": "k"}
        )
    )

    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"username": "username_required"}
