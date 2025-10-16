"Config flow for the e3dc rscp connect integration."

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN  # Konstante in const.py


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
        return None  # Optional: Für Optionen nach Einrichtung
