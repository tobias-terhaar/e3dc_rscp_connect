"Config flow for the e3dc rscp connect integration."

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class E3DCRscpConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for e3dc_rscp_connect integration."""

    VERSION = 1

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
                    vol.Required("port"): int,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("key"): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler if needed."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow for the integration."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

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
                    vol.Required("port", default=current.get("port", 5033)): int,
                    vol.Required("username", default=current.get("username", "")): str,
                    vol.Required("password", default=current.get("password", "")): str,
                    vol.Required("key", default=current.get("key", "")): str,
                    vol.Required(
                        "update_interval", default=current.get("update_interval", "10")
                    ): int,
                }
            ),
        )
