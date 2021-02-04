import logging
import threading
from homeassistant import config_entries
from homeassistant.components.zeroconf import async_get_instance
from homeassistant.const import CONF_HOST
import voluptuous as vol
from libdyson.dyson_360_eye import Dyson360Eye
from libdyson.discovery import DysonDiscovery
from libdyson.const import DEVICE_TYPE_360_EYE
from libdyson.exceptions import DysonException
from .const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_SERIAL, DOMAIN, DEVICE_TYPE_NAMES

_LOGGER = logging.getLogger(__name__)


DISCOVERY_TIMEOUT = 10

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
            device = Dyson360Eye(serial, info[CONF_CREDENTIAL])
            host = info.get(CONF_HOST)


            # Find device using discovery
            if not host:
                discovered = threading.Event()
                def _callback(address: str) -> None:
                    _LOGGER.debug("Found device at %s", address)
                    nonlocal host
                    host = address
                    discovered.set()
                discovery = DysonDiscovery()
                discovery.register_device(device, _callback)
                discovery.start_discovery(
                    await async_get_instance(self.hass)
                )
                if not await self.hass.async_add_executor_job(
                    discovered.wait, DISCOVERY_TIMEOUT
                ):
                    _LOGGER.debug("Discovery timed out")
                    errors["base"] = "cannot_connect"
                discovery.stop_discovery()

            # Try connect to the device
            if host:
                try:
                    device.connect(host)
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
                            CONF_DEVICE_TYPE: device_type,
                            CONF_HOST: info.get(CONF_HOST),
                        }
                    )

        info = info or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SERIAL, default=info.get(CONF_SERIAL, "")): str,
                vol.Required(CONF_CREDENTIAL, default=info.get(CONF_CREDENTIAL, "")): str,
                vol.Required(CONF_DEVICE_TYPE, default=info.get(CONF_DEVICE_TYPE, "")): vol.In(DEVICE_TYPE_NAMES),
                vol.Optional(CONF_HOST, default=info.get(CONF_HOST, "")): str,
            }),
            errors=errors,
        )
