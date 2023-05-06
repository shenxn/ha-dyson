"""Dyson climate platform."""

import logging
from typing import Any

from libdyson import DysonPureHotCoolLink

from homeassistant.components.climate import (
    FAN_DIFFUSE,
    FAN_FOCUS,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

HVAC_MODES = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]
FAN_MODES = [FAN_FOCUS, FAN_DIFFUSE]
SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE
SUPPORT_FLAGS_LINK = SUPPORT_FLAGS | ClimateEntityFeature.FAN_MODE


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dyson climate from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    if isinstance(device, DysonPureHotCoolLink):
        async_add_entities([DysonPureHotCoolLinkEntity(device, name)])
    else:  # DysonPureHotCool
        async_add_entities([DysonPureHotCoolEntity(device, name)])


class DysonClimateEntity(DysonEntity, ClimateEntity):
    """Dyson climate entity base class."""

    _attr_supported_features = SUPPORT_FLAGS
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = HVAC_MODES

    @property
    def hvac_mode(self) -> str:
        """Return hvac operation."""
        if not self._device.is_on:
            return HVACMode.OFF
        if self._device.heat_mode_is_on:
            return HVACMode.HEAT
        return HVACMode.COOL

    @property
    def hvac_action(self) -> str:
        """Return the current running hvac operation."""
        if not self._device.is_on:
            return HVACAction.OFF
        if self._device.heat_mode_is_on:
            if self._device.heat_status_is_on:
                return HVACAction.HEATING
            return HVACAction.IDLE
        return HVACAction.COOLING

    @property
    def target_temperature(self) -> int:
        """Return the target temperature."""
        return self._device.heat_target - 273

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if (value := self._device.temperature) >= 0:
            return float(f"{(value - 273.15):.1f}")
        return None

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        if (value := self._device.humidity) >= 0:
            return value
        return None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 1

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 37

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            _LOGGER.error("Missing target temperature %s", kwargs)
            return
        _LOGGER.debug("Set %s temperature %s", self.name, target_temp)
        # Limit the target temperature into acceptable range.
        target_temp = min(self.max_temp, target_temp)
        target_temp = max(self.min_temp, target_temp)
        self._device.set_heat_target(target_temp + 273)

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new hvac mode."""
        _LOGGER.debug("Set %s heat mode %s", self.name, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            self._device.turn_off()
        elif not self._device.is_on:
            self._device.turn_on()
        if hvac_mode == HVACMode.HEAT:
            self._device.enable_heat_mode()
        elif hvac_mode == HVACMode.COOL:
            self._device.disable_heat_mode()


class DysonPureHotCoolLinkEntity(DysonClimateEntity):
    """Dyson Pure Hot+Cool Link entity."""

    _attr_fan_modes = FAN_MODES
    _attr_supported_features = SUPPORT_FLAGS_LINK

    @property
    def fan_mode(self) -> str:
        """Return the fan setting."""
        if self._device.focus_mode:
            return FAN_FOCUS
        return FAN_DIFFUSE

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode of the device."""
        _LOGGER.debug("Set %s focus mode %s", self.name, fan_mode)
        if fan_mode == FAN_FOCUS:
            self._device.enable_focus_mode()
        elif fan_mode == FAN_DIFFUSE:
            self._device.disable_focus_mode()


class DysonPureHotCoolEntity(DysonClimateEntity):
    """Dyson Pure Hot+Cool entity."""
