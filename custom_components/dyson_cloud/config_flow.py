import logging
import threading
from typing import Optional
from homeassistant import config_entries
from homeassistant.components.zeroconf import async_get_instance
from homeassistant.const import CONF_EMAIL, CONF_HOST, CONF_PASSWORD, CONF_USERNAME
import voluptuous as vol
from libdyson.cloud import DysonAccount
from libdyson.dyson_360_eye import Dyson360Eye
from libdyson.discovery import DysonDiscovery
from libdyson.const import DEVICE_TYPE_360_EYE
from libdyson.exceptions import DysonException, DysonLoginFailure, DysonNetworkError
from voluptuous.schema_builder import Required

from .const import CONF_AUTH, CONF_LANGUAGE, DOMAIN

_LOGGER = logging.getLogger(__name__)


DISCOVERY_TIMEOUT = 10

class DysonCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Dyson cloud config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, info: Optional[dict]):
        errors = {}
        if info is not None:
            language = info[CONF_LANGUAGE]
            email = info[CONF_EMAIL]
            unique_id = f"{language}_{email}"
            for entry in self._async_current_entries():
                if entry.unique_id == unique_id:
                    return self.async_abort(reason="already_configured")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            account = DysonAccount(language)
            try:
                await self.hass.async_add_executor_job(
                    account.login, email, info[CONF_PASSWORD]
                )
            except DysonNetworkError:
                errors["base"] = "cannot_connect"
            except DysonLoginFailure:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title=f"{email} ({language})",
                    data={
                        CONF_LANGUAGE: language,
                        CONF_AUTH: account.auth_info,
                    }
                )
            

        info = info or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL, default=info.get(CONF_EMAIL, "")): str,
                vol.Required(CONF_PASSWORD, default=info.get(CONF_PASSWORD, "")): str,
                vol.Required(CONF_LANGUAGE, default=info.get(CONF_LANGUAGE, "")): str,
            }),
            errors=errors,
        )
