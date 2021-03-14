"""Humidifier platform for Dyson."""

import logging
from typing import List, Callable

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.humidifier import HumidifierEntity, SUPPORT_MODES, DEVICE_CLASS_HUMIDIFIER
from homeassistant.components.humidifier.const import MODE_NORMAL, MODE_AUTO
from homeassistant.const import CONF_NAME
from homeassistant.helpers import entity_platform

from libdyson import MessageType, DysonPureHumidityCool, WaterHardness

from . import DysonEntity
from .const import DOMAIN, DATA_DEVICES

_LOGGER = logging.getLogger(__name__)

AVAILABLE_MODES = [MODE_NORMAL, MODE_AUTO]

MIN_HUMIDITY = 30  # Not sure about this
MAX_HUMIDITY = 100  # Not sure about this

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

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_HUMIDIFIER

    @property
    def is_on(self) -> bool:
        return self._device.humidification

    @property
    def min_humidity(self) -> int:
        return MIN_HUMIDITY

    @property
    def max_humidity(self) -> int:
        return MAX_HUMIDITY
    
    @property
    def target_humidity(self) -> int:
        return self._device.humidity_target

    @property
    def available_modes(self) -> List[str]:
        return AVAILABLE_MODES

    @property
    def mode(self) -> str:
        return MODE_AUTO if self._device.humidification_auto_mode else MODE_NORMAL

    @property
    def supported_features(self) -> int:
        return SUPPORT_MODES

    def turn_on(self, **kwargs) -> None:
        self._device.enable_humidification()

    def turn_off(self, **kwargs) -> None:
        self._device.disable_humidification()

    def set_humidity(self, humidity: int) -> None:
        self._device.set_humidity_target(humidity)

    def set_mode(self, mode: str) -> None:
        if mode == MODE_AUTO:
            self._device.enable_humidification_auto_mode()
        elif mode == MODE_NORMAL:
            self._device.disable_humidification_auto_mode()
        _LOGGER.error("%s is not a valid mode.", mode)

    def set_water_hardness(self, water_hardness: str) -> None:
        self._device.set_water_hardness(WATER_HARDNESS_STR_TO_ENUM[water_hardness])
