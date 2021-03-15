"""Humidifier platform for Dyson."""

import logging
from typing import Callable, List

from libdyson import MessageType, WaterHardness
import voluptuous as vol

from homeassistant.components.humidifier import (
    DEVICE_CLASS_HUMIDIFIER,
    SUPPORT_MODES,
    HumidifierEntity,
)
from homeassistant.components.humidifier.const import MODE_AUTO, MODE_NORMAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

AVAILABLE_MODES = [MODE_NORMAL, MODE_AUTO]

MIN_HUMIDITY = 30  # Not sure about this
MAX_HUMIDITY = 70  # Not sure about this

SUPPORTED_FEATURES = SUPPORT_MODES

ATTR_WATER_HARDNESS = "water_hardness"

SERVICE_SET_WATER_HARDNESS = "set_water_hardness"

WATER_HARDNESS_STR_TO_ENUM = {
    "soft": WaterHardness.SOFT,
    "medium": WaterHardness.MEDIUM,
    "hard": WaterHardness.HARD,
}

SET_WATER_HARDNESS_SCHEMA = {
    vol.Required(ATTR_WATER_HARDNESS): vol.In(WATER_HARDNESS_STR_TO_ENUM)
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson humidifier from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    async_add_entities([DysonHumidifierEntity(device, name)])

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_WATER_HARDNESS, SET_WATER_HARDNESS_SCHEMA, "set_water_hardness"
    )


class DysonHumidifierEntity(DysonEntity, HumidifierEntity):
    """Dyson humidifier entity."""

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def device_class(self) -> str:
        """Return device class."""
        return DEVICE_CLASS_HUMIDIFIER

    @property
    def is_on(self) -> bool:
        """Return if humidification is on."""
        return self._device.humidification

    @property
    def min_humidity(self) -> int:
        """Return the minimum target humidity."""
        return MIN_HUMIDITY

    @property
    def max_humidity(self) -> int:
        """Return the maximum target humidity."""
        return MAX_HUMIDITY

    @property
    def target_humidity(self) -> int:
        """Return the target."""
        return self._device.target_humidity

    @property
    def available_modes(self) -> List[str]:
        """Return available modes."""
        return AVAILABLE_MODES

    @property
    def mode(self) -> str:
        """Return current mode."""
        return MODE_AUTO if self._device.humidification_auto_mode else MODE_NORMAL

    @property
    def supported_features(self) -> int:
        """Return supported features."""
        return SUPPORT_MODES

    def turn_on(self, **kwargs) -> None:
        """Turn on humidification."""
        self._device.enable_humidification()

    def turn_off(self, **kwargs) -> None:
        """Turn off humidification."""
        self._device.disable_humidification()

    def set_humidity(self, humidity: int) -> None:
        """Set target humidity."""
        self._device.set_target_humidity(humidity)

    def set_mode(self, mode: str) -> None:
        """Set humidification mode."""
        if mode == MODE_AUTO:
            self._device.enable_humidification_auto_mode()
        elif mode == MODE_NORMAL:
            self._device.disable_humidification_auto_mode()
        _LOGGER.error("%s is not a valid mode.", mode)

    def set_water_hardness(self, water_hardness: str) -> None:
        """Set water hardness."""
        self._device.set_water_hardness(WATER_HARDNESS_STR_TO_ENUM[water_hardness])
