"""Fan platform for dyson."""

from homeassistant.const import CONF_NAME
import logging
import math

from typing import Callable, List, Optional
from homeassistant.components.fan import FanEntity, SUPPORT_OSCILLATE, SUPPORT_SET_SPEED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from libdyson import FanSpeed

from . import DysonEntity, DOMAIN
from .const import DATA_DEVICES

_LOGGER = logging.getLogger(__name__)

ATTR_NIGHT_MODE = "night_mode"

PRESET_MODE_AUTO = "auto"
PRESET_MODES = [PRESET_MODE_AUTO]

ORDERED_DYSON_SPEEDS = [
    FanSpeed.SPEED_1,
    FanSpeed.SPEED_2,
    FanSpeed.SPEED_3,
    FanSpeed.SPEED_4,
    FanSpeed.SPEED_5,
    FanSpeed.SPEED_6,
    FanSpeed.SPEED_7,
    FanSpeed.SPEED_8,
    FanSpeed.SPEED_9,
    FanSpeed.SPEED_10,
]
DYSON_SPEED_TO_INT_VALUE = {k: int(k.value) for k in ORDERED_DYSON_SPEEDS}
INT_VALUE_TO_DYSON_SPEED = {v: k for k, v in DYSON_SPEED_TO_INT_VALUE.items()}

SPEED_LIST_DYSON = list(DYSON_SPEED_TO_INT_VALUE.values())

SPEED_RANGE = (
    SPEED_LIST_DYSON[0],
    SPEED_LIST_DYSON[-1],
)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson fan from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    entity = DysonPureCoolLinkEntity(device, config_entry.data[CONF_NAME])
    async_add_entities([entity])


class DysonPureCoolLinkEntity(DysonEntity, FanEntity):

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device.is_on

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        if self._device.auto_mode:
            return None
        return ranged_value_to_percentage(SPEED_RANGE, int(self._device.speed.value))

    @property
    def preset_modes(self) -> List[str]:
        """Return the available preset modes."""
        return PRESET_MODES

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode."""
        if self._device.auto_mode:
            return PRESET_MODE_AUTO
        return None

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._device.oscillation

    @property
    def night_mode(self) -> bool:
        """Return if night mode is on."""
        return self._device.night_mode

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_OSCILLATE | SUPPORT_SET_SPEED

    @property
    def device_state_attributes(self) -> dict:
        """Return optional state attributes."""
        return {
            ATTR_NIGHT_MODE: self.night_mode,
        }

    def turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Turn on the fan."""
        _LOGGER.debug("Turn on fan %s with percentage %s", self.name, percentage)
        if preset_mode:
            self.set_preset_mode(preset_mode)
        elif percentage is None:
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
        if percentage == 0:
            self.turn_off()
            return
        dyson_speed = INT_VALUE_TO_DYSON_SPEED[
            math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        ]
        self._device.set_speed(dyson_speed)

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set a preset mode on the fan."""
        self._valid_preset_mode_or_raise(preset_mode)
        # There currently is only one
        self._device.set_auto_mode(True)

    def oscillate(self, oscillating: bool) -> None:
        """Turn on/of oscillation."""
        _LOGGER.debug("Turn oscillation %s for device %s", oscillating, self.name)
        self._device.set_oscillation(oscillating)
