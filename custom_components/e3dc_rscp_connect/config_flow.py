"Config flow for the e3dc rscp connect integration."

import asyncio
import logging
from urllib.parse import urlparse

import aiohttp
import voluptuous as vol
from defusedxml import ElementTree
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_SERIAL,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from .const import (
    CONF_HOST,
    CONF_KEY,
    CONF_LOGIN_TYPE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    LOCAL_USERNAME,
    LOGIN_TYPE_LOCAL,
    LOGIN_TYPE_PORTAL,
    RSCP_SERVICE_NAME,
)

_LOGGER = logging.getLogger(__name__)

# The device description is a small XML document, no need to wait long for it.
DESCRIPTION_TIMEOUT = 10

# The login type is part of the credentials form instead of a separate menu
# step, so it can still be changed when a half finished flow is resumed.
LOGIN_TYPE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[LOGIN_TYPE_LOCAL, LOGIN_TYPE_PORTAL],
        translation_key="login_type",
        mode=SelectSelectorMode.DROPDOWN,
    )
)


def parse_rscp_port(xml: str) -> int | None:
    """Extract the RSCP port from a UPnP device description document.

    The E3/DC device description lists its services in ``serviceList``; the one
    named ``RSCP_SERVICE_PROVIDER`` carries the RSCP port in a ``PORT`` element.
    Returns ``None`` if the document cannot be parsed or holds no RSCP service.
    """
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as err:
        _LOGGER.debug("Could not parse device description: %s", err)
        return None

    for service in root.iter():
        # Tags are namespaced (urn:schemas-upnp-org:device-1-0), match local name.
        if service.tag.rpartition("}")[2] != "service":
            continue
        if service.get("name") != RSCP_SERVICE_NAME:
            continue
        for child in service:
            if child.tag.rpartition("}")[2] != "PORT" or not child.text:
                continue
            try:
                return int(child.text.strip())
            except ValueError:
                _LOGGER.debug("Invalid RSCP port in device description: %s", child.text)
                return None

    return None


def credentials_schema(
    *,
    include_host: bool,
    include_port: bool,
    include_update_interval: bool = False,
    defaults: dict | None = None,
) -> vol.Schema:
    """Build the credentials form.

    The username is only needed for a portal login, so it is optional here and
    validated by :func:`credentials_errors`.
    """
    defaults = defaults or {}

    def key(name: str, fallback=None, marker=vol.Required):
        default = defaults.get(name, fallback)
        if default is None:
            return marker(name)
        return marker(name, default=default)

    schema: dict = {key(CONF_LOGIN_TYPE, LOGIN_TYPE_LOCAL): LOGIN_TYPE_SELECTOR}
    if include_host:
        schema[key(CONF_HOST)] = str
    if include_port:
        schema[key(CONF_PORT, DEFAULT_PORT)] = int
    schema[key(CONF_USERNAME, marker=vol.Optional)] = str
    schema[key(CONF_PASSWORD)] = str
    schema[key(CONF_KEY)] = str
    if include_update_interval:
        schema[key(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)] = int

    return vol.Schema(schema)


def credentials_errors(user_input: dict) -> dict[str, str]:
    """Validate the submitted credentials, keyed by form field."""
    if (
        user_input.get(CONF_LOGIN_TYPE) == LOGIN_TYPE_PORTAL
        and not (user_input.get(CONF_USERNAME) or "").strip()
    ):
        return {CONF_USERNAME: "username_required"}

    return {}


def form_defaults(config, *, keep_secrets: bool = True) -> dict:
    """Turn a stored configuration into defaults for the credentials form.

    Entries configured before the login type was stored are recognized by
    their username; the fixed local user is never shown in the form.
    """
    defaults = dict(config)

    if not keep_secrets:
        defaults.pop(CONF_PASSWORD, None)
        defaults.pop(CONF_KEY, None)

    if defaults.get(CONF_USERNAME) == LOCAL_USERNAME:
        defaults.pop(CONF_USERNAME, None)
        defaults.setdefault(CONF_LOGIN_TYPE, LOGIN_TYPE_LOCAL)
    else:
        defaults.setdefault(CONF_LOGIN_TYPE, LOGIN_TYPE_PORTAL)

    return defaults


def entry_data(user_input: dict) -> dict:
    """Build the entry data from the submitted form.

    A local login ignores the username field, it always authenticates as
    ``LOCAL_USERNAME``.
    """
    data = dict(user_input)
    login_type = data.get(CONF_LOGIN_TYPE, LOGIN_TYPE_LOCAL)
    data[CONF_LOGIN_TYPE] = login_type
    if login_type == LOGIN_TYPE_LOCAL:
        data[CONF_USERNAME] = LOCAL_USERNAME
    else:
        data[CONF_USERNAME] = (data.get(CONF_USERNAME) or "").strip()
    return data


class E3DCRscpConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for e3dc_rscp_connect integration."""

    # VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    async def async_step_user(self, user_input=None):
        """Handle the manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = credentials_errors(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=entry_data(user_input)
                )

        return self.async_show_form(
            step_id="user",
            data_schema=credentials_schema(
                include_host=True, include_port=True, defaults=user_input
            ),
            errors=errors,
        )

    async def async_step_ssdp(self, discovery_info: SsdpServiceInfo):
        """Handle a device discovered via SSDP."""
        host = (
            urlparse(discovery_info.ssdp_location).hostname
            if discovery_info.ssdp_location
            else None
        )

        unique_id = discovery_info.upnp.get(
            ATTR_UPNP_SERIAL
        ) or discovery_info.upnp.get(ATTR_UPNP_UDN)

        if not unique_id or not host:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._discovered_host = host
        self._discovered_name = discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME, host)
        self._discovered_port = (
            await self._async_fetch_rscp_port(discovery_info.ssdp_location)
            or DEFAULT_PORT
        )

        _LOGGER.debug(
            "Discovered %s at %s, RSCP port %s",
            self._discovered_name,
            host,
            self._discovered_port,
        )

        self.context["title_placeholders"] = {
            "name": self._discovered_name,
            "host": self._discovered_host,
        }
        return await self.async_step_discovery_confirm()

    async def _async_fetch_rscp_port(self, location: str | None) -> int | None:
        """Read the RSCP port from the device description at ``location``."""
        if not location:
            return None

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                location, timeout=aiohttp.ClientTimeout(total=DESCRIPTION_TIMEOUT)
            ) as response:
                response.raise_for_status()
                xml = await response.text(errors="replace")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug(
                "Could not load device description from %s: %s", location, err
            )
            return None

        return parse_rscp_port(xml)

    async def async_step_discovery_confirm(self, user_input=None):
        """Ask for the credentials of an SSDP-discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = credentials_errors(user_input)
            if not errors:
                data = entry_data(user_input)
                data[CONF_HOST] = self._discovered_host
                data.setdefault(CONF_PORT, self._discovered_port)
                return self.async_create_entry(title=self._discovered_name, data=data)

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=credentials_schema(
                include_host=False, include_port=False, defaults=user_input
            ),
            description_placeholders=self._discovery_placeholders(),
            errors=errors,
        )

    def _discovery_placeholders(self) -> dict[str, str]:
        """Placeholders describing the discovered device."""
        return {
            "name": self._discovered_name or "",
            "host": self._discovered_host or "",
            "port": str(self._discovered_port),
        }

    async def async_step_reauth(self, entry_data):
        """Handle credentials the device rejected."""
        entry = self._get_reauth_entry()
        # Home Assistant only fills in the name, but flow_title also needs the
        # host - without it the frontend can't render the title at all.
        self.context["title_placeholders"] = {
            "name": entry.title,
            "host": (entry.options or entry.data).get(CONF_HOST, ""),
        }
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for new credentials and reload the entry with them."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = credentials_errors(user_input)
            if not errors:
                credentials = entry_data(user_input)
                # The coordinator reads the options and falls back to the data,
                # so the new credentials have to reach whichever is in use.
                if entry.options:
                    return self.async_update_reload_and_abort(
                        entry,
                        data={**entry.data, **credentials},
                        options={**entry.options, **credentials},
                    )
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, **credentials}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=credentials_schema(
                include_host=False,
                include_port=False,
                defaults=user_input
                or form_defaults(entry.options or entry.data, keep_secrets=False),
            ),
            description_placeholders={
                "name": entry.title,
                "host": (entry.options or entry.data).get(CONF_HOST, ""),
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler if needed."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = credentials_errors(user_input)
            if not errors:
                return self.async_create_entry(title="", data=entry_data(user_input))

        return self.async_show_form(
            step_id="init",
            data_schema=credentials_schema(
                include_host=True,
                include_port=True,
                include_update_interval=True,
                defaults=user_input or self._current_values(),
            ),
            errors=errors,
        )

    @callback
    def _current_values(self) -> dict:
        """Current configuration, used as the defaults of the options form."""
        # Aktuelle Werte aus Optionen oder Fallback auf ursprüngliche Konfiguration
        return form_defaults(self.config_entry.options or self.config_entry.data)
