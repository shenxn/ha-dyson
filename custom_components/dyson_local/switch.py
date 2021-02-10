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
    name = config_entry.data[CONF_NAME]
    entities = [
        DysonNightModeSwitchEntity(device, name),
        DysonContinuousMonitoringSwitchEntity(device, name)
    ]
    async_add_entities(entities)


class DysonNightModeSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson fan night mode switch."""

    @property
    def sub_name(self):
        """Return the name of the entity."""
        return "Night Mode"

    @property
    def sub_unique_id(self):
        """Return the unique id of the entity."""
        return "night-mode"

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


class DysonContinuousMonitoringSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson fan continuous monitoring."""

    @property
    def sub_name(self):
        """Return the name of the entity."""
        return "Continuous Monitoring"

    @property
    def sub_unique_id(self):
        """Return the unique id of the entity."""
        return "continuous monitoring"

    @property
    def icon(self):
        """Return the icon of the entity."""
        return "mdi:eye" if self.is_on else "mdi:eye-off"

    @property
    def is_on(self):
        """Return if continuous monitoring is on."""
        return self._device.continuous_monitoring

    def turn_on(self):
        """Turn on continuous monitoring."""
        return self._device.set_continuous_monitoring(True)

    def turn_off(self):
        """Turn off continuous monitoring."""
        return self._device.set_continuous_monitoring(False)
