"""Fan platform for dyson."""

import logging
import math
from typing import Callable, Optional

from libdyson import (
    DysonPureCool,
    DysonPureCoolLink,
    HumidifyOscillationMode,
    MessageType,
)
from libdyson.const import AirQualityTarget
import voluptuous as vol

from homeassistant.components.fan import SUPPORT_OSCILLATE, SUPPORT_SET_SPEED, FanEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.util.percentage import (
    int_states_in_range,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import DOMAIN, DysonEntity
from .const import DATA_DEVICES

_LOGGER = logging.getLogger(__name__)

AIR_QUALITY_TARGET_ENUM_TO_STR = {
    AirQualityTarget.OFF: "off",
    AirQualityTarget.GOOD: "good",
    AirQualityTarget.DEFAULT: "default",
    AirQualityTarget.SENSITIVE: "sensitive",
    AirQualityTarget.VERY_SENSITIVE: "very sensitive",
}
AIR_QUALITY_TARGET_STR_TO_ENUM = {
    value: key for key, value in AIR_QUALITY_TARGET_ENUM_TO_STR.items()
}

OSCILLATION_MODE_ENUM_TO_STR = {
    HumidifyOscillationMode.DEGREE_45: "45",
    HumidifyOscillationMode.DEGREE_90: "90",
    HumidifyOscillationMode.BREEZE: "breeze",
}
OSCILLATION_MODE_STR_TO_ENUM = {
    value: key for key, value in OSCILLATION_MODE_ENUM_TO_STR.items()
}

ATTR_AIR_QUALITY_TARGET = "air_quality_target"
ATTR_ANGLE_LOW = "angle_low"
ATTR_ANGLE_HIGH = "angle_high"
ATTR_OSCILLATION_MODE = "oscillation_mode"
ATTR_TIMER = "timer"

SERVICE_SET_AIR_QUALITY_TARGET = "set_air_quality_target"
SERVICE_SET_ANGLE = "set_angle"
SERVICE_SET_OSCILLATION_MODE = "set_oscillation_mode"
SERVICE_SET_TIMER = "set_timer"

SET_AIR_QUALITY_TARGET_SCHEMA = {
    vol.Required(ATTR_AIR_QUALITY_TARGET): vol.In(AIR_QUALITY_TARGET_STR_TO_ENUM),
}

SET_ANGLE_SCHEMA = {
    vol.Required(ATTR_ANGLE_LOW): cv.positive_int,
    vol.Required(ATTR_ANGLE_HIGH): cv.positive_int,
}

SET_OSCILLATION_MODE_SCHEMA = {
    vol.Required(ATTR_OSCILLATION_MODE): vol.In(OSCILLATION_MODE_STR_TO_ENUM),
}

SET_TIMER_SCHEMA = {
    vol.Required(ATTR_TIMER): cv.positive_int,
}

SPEED_LIST_DYSON = list(range(1, 11))  # 1, 2, ..., 10

SPEED_RANGE = (
    SPEED_LIST_DYSON[0],
    SPEED_LIST_DYSON[-1],
)

SUPPORTED_FEATURES = SUPPORT_OSCILLATE | SUPPORT_SET_SPEED


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson fan from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    if isinstance(device, DysonPureCoolLink):
        entity = DysonPureCoolLinkEntity(device, name)
    elif isinstance(device, DysonPureCool):
        entity = DysonPureCoolEntity(device, name)
    else:  # DysonPureHumidityCool
        entity = DysonPureHumidifyCoolEntity(device, name)
    async_add_entities([entity])

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_TIMER, SET_TIMER_SCHEMA, "set_timer"
    )
    if isinstance(device, DysonPureCoolLink):
        platform.async_register_entity_service(
            SERVICE_SET_AIR_QUALITY_TARGET,
            SET_AIR_QUALITY_TARGET_SCHEMA,
            "set_air_quality_target",
        )
    elif isinstance(device, DysonPureCool):
        platform.async_register_entity_service(
            SERVICE_SET_ANGLE, SET_ANGLE_SCHEMA, "set_angle"
        )
    else:  # DysonPureHumidityCool
        platform.async_register_entity_service(
            SERVICE_SET_OSCILLATION_MODE,
            SET_OSCILLATION_MODE_SCHEMA,
            "set_oscillation_mode",
        )


class DysonFanEntity(DysonEntity, FanEntity):
    """Dyson fan entity base class."""

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device.is_on

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return int_states_in_range(SPEED_RANGE)

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._device.speed is None:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, int(self._device.speed))

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._device.oscillation

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORTED_FEATURES

    def turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Turn on the fan."""
        _LOGGER.debug("Turn on fan %s with percentage %s", self.name, percentage)
        if percentage is None:
            # percentage not set, just turn on
            self._device.turn_on()
        else:
            self.set_percentage(percentage)

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        _LOGGER.debug("Turn off fan %s", self.name)
        return self._device.turn_off()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        dyson_speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._device.set_speed(dyson_speed)

    def oscillate(self, oscillating: bool) -> None:
        """Turn on/of oscillation."""
        _LOGGER.debug("Turn oscillation %s for device %s", oscillating, self.name)
        if oscillating:
            self._device.enable_oscillation()
        else:
            self._device.disable_oscillation()

    def set_timer(self, timer: int) -> None:
        """Set sleep timer."""
        if timer == 0:
            self._device.disable_sleep_timer()
        self._device.set_sleep_timer(timer)


class DysonPureCoolLinkEntity(DysonFanEntity):
    """Dyson Pure Cool Link entity."""

    @property
    def air_quality_target(self) -> str:
        """Return air quality target."""
        return AIR_QUALITY_TARGET_ENUM_TO_STR[self._device.air_quality_target]

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        return {ATTR_AIR_QUALITY_TARGET: self.air_quality_target}

    def set_air_quality_target(self, air_quality_target: str) -> None:
        """Set air quality target."""
        self._device.set_air_quality_target(
            AIR_QUALITY_TARGET_STR_TO_ENUM[air_quality_target]
        )


class DysonPureCoolEntity(DysonFanEntity):
    """Dyson Pure Cool entity."""

    @property
    def angle_low(self) -> int:
        """Return oscillation angle low."""
        return self._device.oscillation_angle_low

    @property
    def angle_high(self) -> int:
        """Return oscillation angle high."""
        return self._device.oscillation_angle_high

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        return {
            ATTR_ANGLE_LOW: self.angle_low,
            ATTR_ANGLE_HIGH: self.angle_high,
        }

    def set_angle(self, angle_low: int, angle_high: int) -> None:
        """Set oscillation angle."""
        _LOGGER.debug(
            "set low %s and high angle %s for device %s",
            angle_low,
            angle_high,
            self.name,
        )
        self._device.enable_oscillation(angle_low, angle_high)


class DysonPureHumidifyCoolEntity(DysonFanEntity):
    """Dyson Pure Humidify+Cool entity."""

    @property
    def oscillation_mode(self) -> str:
        """Return oscillation mode."""
        return OSCILLATION_MODE_ENUM_TO_STR[self._device.oscillation_mode]

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        return {ATTR_OSCILLATION_MODE: self.oscillation_mode}

    def set_oscillation_mode(self, oscillation_mode: str) -> None:
        """Set oscillation mode."""
        _LOGGER.debug(
            "set oscillation mode %s for device %s",
            oscillation_mode,
            self.name,
        )
        self._device.enable_oscillation(OSCILLATION_MODE_STR_TO_ENUM[oscillation_mode])
