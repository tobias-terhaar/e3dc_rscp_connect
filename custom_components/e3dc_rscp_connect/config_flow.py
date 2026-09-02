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
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_SERIAL,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from .const import DEFAULT_PORT, DOMAIN, RSCP_SERVICE_NAME

_LOGGER = logging.getLogger(__name__)

# The device description is a small XML document, no need to wait long for it.
DESCRIPTION_TIMEOUT = 10


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


class E3DCRscpConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for e3dc_rscp_connect integration."""

    # VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None
        self._discovered_port: int = DEFAULT_PORT

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Optional: Hier könntest du doppelte Konfigurationen verhindern
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host"): str,
                    vol.Required("port", default=DEFAULT_PORT): int,
                    vol.Required("username", default="local.user"): str,
                    vol.Required("password"): str,
                    vol.Required("key"): str,
                }
            ),
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
        self._abort_if_unique_id_configured(updates={"host": host})

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
        """Ask the user for credentials for an SSDP-discovered device."""
        if user_input is not None:
            data = {
                "host": self._discovered_host,
                "port": self._discovered_port,
                "username": user_input["username"],
                "password": user_input["password"],
                "key": user_input["key"],
            }
            return self.async_create_entry(title=self._discovered_name, data=data)

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema(
                {
                    # vol.Required("port", default=self._discovered_port): int,
                    vol.Required("username", default="local.user"): str,
                    vol.Required("password"): str,
                    vol.Required("key"): str,
                }
            ),
            description_placeholders={
                "name": self._discovered_name or "",
                "host": self._discovered_host or "",
                "port": self._discovered_port or "",
            },
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
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Aktuelle Werte aus Optionen oder Fallback auf ursprüngliche Konfiguration
        current = self.config_entry.options or self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("host", default=current.get("host", "")): str,
                    vol.Required(
                        "port", default=current.get("port", DEFAULT_PORT)
                    ): int,
                    vol.Required("username", default=current.get("username", "")): str,
                    vol.Required("password", default=current.get("password", "")): str,
                    vol.Required("key", default=current.get("key", "")): str,
                    vol.Required(
                        "update_interval", default=current.get("update_interval", "10")
                    ): int,
                }
            ),
        )
