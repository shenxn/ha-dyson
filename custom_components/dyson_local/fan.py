"""Fan platform for dyson."""

from homeassistant.const import CONF_NAME
import logging
import voluptuous as vol

from typing import Callable, List, Optional
from homeassistant.components.fan import FanEntity, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SUPPORT_OSCILLATE, SUPPORT_SET_SPEED
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform, config_validation as cv

from libdyson import FanSpeed
from libdyson.const import MessageType

from . import DysonEntity, DOMAIN
from .const import DATA_DEVICES

_LOGGER = logging.getLogger(__name__)

ATTR_NIGHT_MODE = "night_mode"
ATTR_DYSON_SPEED = "dyson_speed"
ATTR_DYSON_SPEED_LIST = "dyson_speed_list"
ATTR_AUTO_MODE = "auto_mode"

SERVICE_SET_AUTO_MODE = "set_auto_mode"
SERVICE_SET_DYSON_SPEED = "set_speed"

SET_AUTO_MODE_SCHEMA = {
    vol.Required(ATTR_AUTO_MODE): cv.boolean,
}

SET_DYSON_SPEED_SCHEMA = {
    vol.Required(ATTR_DYSON_SPEED): cv.positive_int,
}

SPEED_LIST_HA = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

SPEED_LIST_DYSON = [
    int(FanSpeed.SPEED_1.value),
    int(FanSpeed.SPEED_2.value),
    int(FanSpeed.SPEED_3.value),
    int(FanSpeed.SPEED_4.value),
    int(FanSpeed.SPEED_5.value),
    int(FanSpeed.SPEED_6.value),
    int(FanSpeed.SPEED_7.value),
    int(FanSpeed.SPEED_8.value),
    int(FanSpeed.SPEED_9.value),
    int(FanSpeed.SPEED_10.value),
]

SPEED_DYSON_TO_HA = {
    FanSpeed.SPEED_1: SPEED_LOW,
    FanSpeed.SPEED_2: SPEED_LOW,
    FanSpeed.SPEED_3: SPEED_LOW,
    FanSpeed.SPEED_4: SPEED_LOW,
    FanSpeed.SPEED_AUTO: SPEED_MEDIUM,
    FanSpeed.SPEED_5: SPEED_MEDIUM,
    FanSpeed.SPEED_6: SPEED_MEDIUM,
    FanSpeed.SPEED_7: SPEED_MEDIUM,
    FanSpeed.SPEED_8: SPEED_HIGH,
    FanSpeed.SPEED_9: SPEED_HIGH,
    FanSpeed.SPEED_10: SPEED_HIGH,
}

SPEED_HA_TO_DYSON = {
    SPEED_LOW: FanSpeed.SPEED_4,
    SPEED_MEDIUM: FanSpeed.SPEED_7,
    SPEED_HIGH: FanSpeed.SPEED_10,
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson fan from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    entity = DysonPureCoolLinkEntity(device, config_entry.data[CONF_NAME])
    async_add_entities([entity])

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_AUTO_MODE, SET_AUTO_MODE_SCHEMA, "set_auto_mode"
    )
    platform.async_register_entity_service(
        SERVICE_SET_DYSON_SPEED, SET_DYSON_SPEED_SCHEMA, "service_set_dyson_speed"
    )


class DysonPureCoolLinkEntity(DysonEntity, FanEntity):

    _MESSAGE_TYPE = MessageType.STATE

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device.is_on

    @property
    def speed(self):
        """Return the current speed."""
        return SPEED_DYSON_TO_HA[self._device.speed]

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return SPEED_LIST_HA

    @property
    def dyson_speed(self):
        """Return the current speed."""
        if self._device.speed == FanSpeed.SPEED_AUTO:
            return "AUTO"
        return int(self._device.speed.value)

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
            ATTR_AUTO_MODE: self.auto_mode,
            ATTR_NIGHT_MODE: self.night_mode,
            ATTR_DYSON_SPEED: self.dyson_speed,
            ATTR_DYSON_SPEED_LIST: self.dyson_speed_list,
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
        elif speed is None:
            # percentage not set, just turn on
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

    def set_dyson_speed(self, speed: FanSpeed) -> None:
        """Set the exact speed of the fan."""
        self._device.set_speed(speed)

    def service_set_dyson_speed(self, dyson_speed: str) -> None:
        """Handle the service to set dyson speed."""
        if dyson_speed not in SPEED_LIST_DYSON:
            raise ValueError(f'"{dyson_speed}" is not a valid Dyson speed')
        _LOGGER.debug("Set exact speed to %s", dyson_speed)
        speed = FanSpeed(f"{int(dyson_speed):04d}")
        self.set_dyson_speed(speed)

    def oscillate(self, oscillating: bool) -> None:
        """Turn on/of oscillation."""
        _LOGGER.debug("Turn oscillation %s for device %s", oscillating, self.name)
        self._device.set_oscillation(oscillating)

    def set_auto_mode(self, auto_mode: bool) -> None:
        """Turn auto mode on/off."""
        _LOGGER.debug("Turn auto mode %s for device %s", auto_mode, self.name)
        if auto_mode:
            self._device.set_auto_mode(True)
        else:
            self._device.set_auto_mode(False)
