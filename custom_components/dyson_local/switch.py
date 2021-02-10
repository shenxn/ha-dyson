"""Switch platform for dyson."""

from typing import Callable
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.components.switch import SwitchEntity

from . import DysonEntity
from .const import DOMAIN, DATA_DEVICES

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson switch from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    entity = DysonNightModeSwitchEntity(device, config_entry.data[CONF_NAME])
    async_add_entities([entity])


class DysonNightModeSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson fan night mode switch."""

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{super().name} Night Mode"

    @property
    def icon(self):
        """Return the icon of the entity."""
        return "mdi:power-sleep"

    @property
    def is_on(self):
        """Return if night mode is on."""
        return self._device.night_mode

    def turn_on(self):
        """Turn on night mode."""
        return self._device.set_night_mode(True)

    def turn_off(self):
        """Turn off night mode."""
        return self._device.set_night_mode(False)
