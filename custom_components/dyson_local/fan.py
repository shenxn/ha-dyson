"""Fan platform for dyson."""

import logging
import math
from typing import Callable, List, Optional

from libdyson import DysonPureCool, DysonPureCoolLink, MessageType
import voluptuous as vol

from homeassistant.components.fan import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
    NotValidPresetModeError,
)
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

ATTR_ANGLE_LOW = "angle_low"
ATTR_ANGLE_HIGH = "angle_high"
ATTR_TIMER = "timer"

SERVICE_SET_ANGLE = "set_angle"
SERVICE_SET_TIMER = "set_timer"

SET_ANGLE_SCHEMA = {
    vol.Required(ATTR_ANGLE_LOW): cv.positive_int,
    vol.Required(ATTR_ANGLE_HIGH): cv.positive_int,
}

SET_TIMER_SCHEMA = {
    vol.Required(ATTR_TIMER): cv.positive_int,
}

PRESET_MODE_AUTO = "Auto"

SUPPORTED_PRESET_MODES = [PRESET_MODE_AUTO]

SPEED_RANGE = (1, 10)

COMMON_FEATURES = SUPPORT_OSCILLATE | SUPPORT_SET_SPEED | SUPPORT_PRESET_MODE


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
    if isinstance(device, DysonPureCool):
        platform.async_register_entity_service(
            SERVICE_SET_ANGLE, SET_ANGLE_SCHEMA, "set_angle"
        )


class DysonFanEntity(DysonEntity, FanEntity):
    """Dyson fan entity base class."""

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device.is_on

    @property
    def speed(self) -> None:
        """Return None for compatibility with pre-preset_mode state."""
        return None

    @property
    def speed_count(self) -> int:
        """Return the number of different speeds the fan can be set to."""
        return int_states_in_range(SPEED_RANGE)

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._device.speed is None:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, int(self._device.speed))

    def set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0 and not self._device.auto_mode:
            self._device.turn_off()
            return

        dyson_speed = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        self._device.set_speed(dyson_speed)

    @property
    def preset_modes(self) -> List[str]:
        """Return the preset modes supported."""
        return SUPPORTED_PRESET_MODES

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current selected preset mode."""
        if self._device.auto_mode:
            return PRESET_MODE_AUTO
        return None

    def set_preset_mode(self, preset_mode: Optional[str]) -> None:
        """Configure the preset mode."""
        if preset_mode is None:
            self._device.disable_auto_mode()
        elif preset_mode == PRESET_MODE_AUTO:
            self._device.enable_auto_mode()
        else:
            raise NotValidPresetModeError(f"Invalid preset mode: {preset_mode}")

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._device.oscillation

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return COMMON_FEATURES

    def turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Turn on the fan."""
        _LOGGER.debug("Turn on fan %s with percentage %s", self.name, percentage)
        self.set_preset_mode(preset_mode)
        if percentage is not None:
            self.set_percentage(percentage)

        self._device.turn_on()

    def turn_off(self, **kwargs) -> None:
        """Turn off the fan."""
        _LOGGER.debug("Turn off fan %s", self.name)
        return self._device.turn_off()

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


class DysonPureCoolEntity(DysonFanEntity):
    """Dyson Pure Cool entity."""

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return COMMON_FEATURES | SUPPORT_DIRECTION

    @property
    def current_direction(self) -> str:
        """Return the current airflow direction."""
        if self._device.front_airflow:
            return DIRECTION_FORWARD
        else:
            return DIRECTION_REVERSE

    def set_direction(self, direction: str) -> None:
        """Configure the airflow direction."""
        if direction == DIRECTION_FORWARD:
            self._device.enable_front_airflow()
        elif direction == DIRECTION_REVERSE:
            self._device.disable_front_airflow()
        else:
            raise ValueError(f"Invalid direction {direction}")

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
    def supported_features(self) -> int:
        """Flag supported features."""
        return COMMON_FEATURES | SUPPORT_DIRECTION

    @property
    def current_direction(self) -> str:
        """Return the current airflow direction."""
        if self._device.front_airflow:
            return DIRECTION_FORWARD
        else:
            return DIRECTION_REVERSE

    def set_direction(self, direction: str) -> None:
        """Configure the airflow direction."""
        if direction == DIRECTION_FORWARD:
            self._device.enable_front_airflow()
        elif direction == DIRECTION_REVERSE:
            self._device.disable_front_airflow()
        else:
            raise ValueError(f"Invalid direction {direction}")
