from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_APP_ID,
    CONF_ENGINE,
    CONF_REGION,
    CONF_SECRET_ID,
    CONF_SECRET_KEY,
    DEFAULT_ENGINE,
    DEFAULT_REGION,
    DOMAIN,
    SUPPORTED_ENGINES,
)


class TencentAsrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return TencentAsrOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_APP_ID]}-{user_input[CONF_SECRET_ID]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Tencent Cloud ASR",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_APP_ID): str,
                vol.Required(CONF_SECRET_ID): str,
                vol.Required(CONF_SECRET_KEY): str,
                vol.Optional(
                    CONF_ENGINE,
                    default=DEFAULT_ENGINE,
                ): vol.In(SUPPORTED_ENGINES),
                vol.Optional(CONF_REGION, default=DEFAULT_REGION): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of the integration."""
        errors = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            return self.async_update_reload_and_abort(
                reconfigure_entry,
                data={**reconfigure_entry.data, **user_input},
            )

        current = reconfigure_entry.data
        schema = vol.Schema(
            {
                vol.Required(CONF_APP_ID, default=current.get(CONF_APP_ID, "")): str,
                vol.Required(
                    CONF_SECRET_ID, default=current.get(CONF_SECRET_ID, "")
                ): str,
                vol.Required(
                    CONF_SECRET_KEY, default=current.get(CONF_SECRET_KEY, "")
                ): str,
                vol.Optional(
                    CONF_ENGINE,
                    default=current.get(CONF_ENGINE, DEFAULT_ENGINE),
                ): vol.In(SUPPORTED_ENGINES),
                vol.Optional(
                    CONF_REGION,
                    default=current.get(CONF_REGION, DEFAULT_REGION),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )


class TencentAsrOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_ENGINE,
                    default=self.config_entry.options.get(
                        CONF_ENGINE, current.get(CONF_ENGINE, DEFAULT_ENGINE)
                    ),
                ): vol.In(SUPPORTED_ENGINES),
                vol.Optional(
                    CONF_REGION,
                    default=self.config_entry.options.get(
                        CONF_REGION, current.get(CONF_REGION, DEFAULT_REGION)
                    ),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)

