"""Support for Dyson devices."""

from homeassistant import config_entries
from homeassistant.exceptions import ConfigEntryNotReady
from libdyson.dyson_device import DysonDevice
from libdyson.exceptions import DysonException
from custom_components.dysonv2.const import CONF_CREDENTIAL, CONF_SERIAL, DEVICE_TYPE_NAMES
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from libdyson.dyson_360_eye import Dyson360Eye

from .const import DOMAIN

PLATFORMS = ["binary_sensor", "sensor", "vacuum"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Dyson integration."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dyson from a config entry."""
    device = Dyson360Eye(entry.data[CONF_SERIAL], entry.data[CONF_CREDENTIAL])
    try:
        device.connect(entry.data[CONF_HOST])
    except DysonException:
        raise ConfigEntryNotReady
    hass.data[DOMAIN][entry.entry_id] = device

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


class DysonEntity(Entity):

    def __init__(self, device: DysonDevice):
        self._device = device

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self._device.add_message_listener(self.schedule_update_ha_state)

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return DEVICE_TYPE_NAMES[self._device.device_type]

    @property
    def unique_id(self) -> str:
        """Return the entity unique id."""
        return self._device.serial

    @property
    def device_info(self) -> dict:
        """Return device info of the entity."""
        return {
            "identifiers": {(DOMAIN, self._device.serial)},
            "name": self.name,
            "manufacturer": "Dyson",
            "model": self._device.device_type,
        }
