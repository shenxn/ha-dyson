"""Sensor platform for dyson."""

from typing import Callable
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import DEVICE_CLASS_BATTERY
from homeassistant.config_entries import ConfigEntry

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson sensor from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    entity = Dyson360EyeBatterySensor(device)
    async_add_entities([entity])


class Dyson360EyeBatterySensor(DysonEntity):

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._device.battery_level

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_BATTERY

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{super().name} battery level"
