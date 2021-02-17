"""Fan platform for dyson."""

from homeassistant.const import CONF_NAME
import logging
from libdyson.const import AirQualityTarget
import voluptuous as vol

from typing import Callable, List, Optional
from homeassistant.components.fan import FanEntity, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SUPPORT_OSCILLATE, SUPPORT_SET_SPEED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform, config_validation as cv

from libdyson import MessageType, DysonPureCoolLink

from . import DysonEntity, DOMAIN
from .const import DATA_DEVICES

_LOGGER = logging.getLogger(__name__)

AIR_QUALITY_TARGET_ENUM_TO_STR = {
    AirQualityTarget.GOOD: "good",
    AirQualityTarget.DEFAULT: "default",
    AirQualityTarget.SENSITIVE: "sensitive",
    AirQualityTarget.VERY_SENSITIVE: "very sensitive",
}

AIR_QUALITY_TARGET_STR_TO_ENUM = {
    value: key
    for key, value in AIR_QUALITY_TARGET_ENUM_TO_STR.items()
}

ATTR_DYSON_SPEED = "dyson_speed"
ATTR_DYSON_SPEED_LIST = "dyson_speed_list"
ATTR_AUTO_MODE = "auto_mode"
ATTR_AIR_QUALITY_TARGET = "air_quality_target"

SERVICE_SET_AUTO_MODE = "set_auto_mode"
SERVICE_SET_DYSON_SPEED = "set_speed"
SERVICE_SET_AIR_QUALITY_TARGET = "set_air_quality_target"

SET_AUTO_MODE_SCHEMA = {
    vol.Required(ATTR_AUTO_MODE): cv.boolean,
}

SET_DYSON_SPEED_SCHEMA = {
    vol.Required(ATTR_DYSON_SPEED): cv.positive_int,
}

SET_AIR_QUALITY_TARGET_SCHEMA = {
    vol.Required(ATTR_AIR_QUALITY_TARGET): vol.In(AIR_QUALITY_TARGET_STR_TO_ENUM),
}

SPEED_LIST_HA = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

SPEED_LIST_DYSON = list(range(1, 11))

SPEED_DYSON_TO_HA = {
    1: SPEED_LOW,
    2: SPEED_LOW,
    3: SPEED_LOW,
    4: SPEED_LOW,
    5: SPEED_MEDIUM,
    6: SPEED_MEDIUM,
    7: SPEED_MEDIUM,
    8: SPEED_HIGH,
    9: SPEED_HIGH,
    10: SPEED_HIGH,
}

SPEED_HA_TO_DYSON = {
    SPEED_LOW: 4,
    SPEED_MEDIUM: 7,
    SPEED_HIGH: 10,
}

SUPPORTED_FEATURES = SUPPORT_OSCILLATE | SUPPORT_SET_SPEED


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson fan from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    if isinstance(device, DysonPureCoolLink):
        entity = DysonPureCoolLinkEntity(device, name)
    else:
        entity = DysonPureCoolEntity(device, name)
    async_add_entities([entity])

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_AUTO_MODE, SET_AUTO_MODE_SCHEMA, "set_auto_mode"
    )
    platform.async_register_entity_service(
        SERVICE_SET_DYSON_SPEED, SET_DYSON_SPEED_SCHEMA, "set_dyson_speed"
    )
    if isinstance(device, DysonPureCoolLink):
        platform.async_register_entity_service(
            SERVICE_SET_AIR_QUALITY_TARGET, SET_AIR_QUALITY_TARGET_SCHEMA, "set_air_quality_target"
        )


class DysonFanEntity(DysonEntity, FanEntity):

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device.is_on

    @property
    def speed(self):
        """Return the current speed."""
        if self._device.speed is None:
            return None
        return SPEED_DYSON_TO_HA[self._device.speed]

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return SPEED_LIST_HA

    @property
    def dyson_speed(self):
        """Return the current speed."""
        return self._device.speed

    @property
    def dyson_speed_list(self) -> list:
        """Get the list of available dyson speeds."""
        return SPEED_LIST_DYSON
    
    @property
    def auto_mode(self):
        """Return auto mode."""
        return self._device.auto_mode

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._device.oscillation

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORTED_FEATURES

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        return {
            ATTR_AUTO_MODE: self.auto_mode,
            ATTR_DYSON_SPEED: self.dyson_speed,
            ATTR_DYSON_SPEED_LIST: self.dyson_speed_list,
        }

    def turn_on(
        self,
        speed: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Turn on the fan."""
        _LOGGER.debug("Turn on fan %s with speed %s", self.name, speed)
        if speed is None:
            # speed not set, just turn on
            self._device.turn_on()
        else:
            self.set_speed(speed)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        _LOGGER.debug("Turn off fan %s", self.name)
        return self._device.turn_off()

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if speed not in SPEED_LIST_HA:
            raise ValueError(f'"{speed}" is not a valid speed')
        _LOGGER.debug("Set fan speed to: %s", speed)
        self.set_dyson_speed(SPEED_HA_TO_DYSON[speed])

    def set_dyson_speed(self, dyson_speed: int) -> None:
        """Set the exact speed of the fan."""
        self._device.set_speed(dyson_speed)

    def oscillate(self, oscillating: bool) -> None:
        """Turn on/of oscillation."""
        _LOGGER.debug("Turn oscillation %s for device %s", oscillating, self.name)
        if oscillating:
            self._device.enable_oscillation()
        else:
            self._device.disable_oscillation()

    def set_auto_mode(self, auto_mode: bool) -> None:
        """Turn auto mode on/off."""
        _LOGGER.debug("Turn auto mode %s for device %s", auto_mode, self.name)
        if auto_mode:
            self._device.enable_auto_mode()
        else:
            self._device.disable_auto_mode()


class DysonPureCoolLinkEntity(DysonFanEntity):
    """Dyson Pure Cool Link entity."""

    @property
    def air_quality_target(self) -> str:
        """Return air quality target."""
        return AIR_QUALITY_TARGET_ENUM_TO_STR[self._device.air_quality_target]

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        attributes = super().device_state_attributes
        attributes[ATTR_AIR_QUALITY_TARGET] = self.air_quality_target
        return attributes

    def set_air_quality_target(self, air_quality_target: str) -> None:
        """Set air quality target."""
        self._device.set_air_quality_target(AIR_QUALITY_TARGET_STR_TO_ENUM[air_quality_target])


class DysonPureCoolEntity(DysonFanEntity):
    """Dyson Pure Cool entity."""
