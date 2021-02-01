import logging
from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_HOST
import voluptuous as vol
from libdyson.dyson_360_eye import Dyson360Eye
from libdyson.const import DEVICE_TYPE_360_EYE
from libdyson.exceptions import DysonException
from .const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_SERIAL, DOMAIN, DEVICE_TYPE_NAMES

_LOGGER = logging.getLogger(__name__)


class DysonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Dyson config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, info):
        errors = {}
        if info is not None:
            serial = info[CONF_SERIAL]
            for entry in self._async_current_entries():
                if entry.unique_id == serial:
                    return self.async_abort(reason="already_configured")

            credential = info[CONF_CREDENTIAL]
            host = info[CONF_HOST]
            device = Dyson360Eye(serial, info[CONF_CREDENTIAL])
            try:
                device.connect(info[CONF_HOST])
            except DysonException as err:
                _LOGGER.debug("Failed to connect to device: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()
                device_type = info[CONF_DEVICE_TYPE]
                device_type_name = DEVICE_TYPE_NAMES[device_type]
                return self.async_create_entry(
                    title=device_type_name,
                    data={
                        CONF_SERIAL: serial,
                        CONF_CREDENTIAL: credential,
                        CONF_HOST: host,
                        CONF_DEVICE_TYPE: device_type,
                    }
                )

        info = info or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SERIAL, default=info.get(CONF_SERIAL, "")): str,
                vol.Required(CONF_CREDENTIAL, default=info.get(CONF_CREDENTIAL, "")): str,
                vol.Required(CONF_HOST, default=info.get(CONF_HOST, "")): str,
                vol.Required(CONF_DEVICE_TYPE, default=info.get(CONF_DEVICE_TYPE, "")): vol.In(DEVICE_TYPE_NAMES),
            }),
            errors=errors,
        )
