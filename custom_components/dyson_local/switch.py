"""Switch platform for dyson."""

from typing import Callable

from libdyson import DysonPureCool, DysonPureHumidifyCool

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson switch from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entities = [
        DysonNightModeSwitchEntity(device, name),
        DysonContinuousMonitoringSwitchEntity(device, name),
        DysonAutoModeSwitchEntity(device, name),
    ]
    if isinstance(device, DysonPureCool) or isinstance(device, DysonPureHumidifyCool):
        entities.append(DysonFrontAirflowSwitchEntity(device, name))
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
        return "night_mode"

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
        return self._device.enable_night_mode()

    def turn_off(self):
        """Turn off night mode."""
        return self._device.disable_night_mode()


class DysonContinuousMonitoringSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson fan continuous monitoring."""

    @property
    def sub_name(self):
        """Return the name of the entity."""
        return "Continuous Monitoring"

    @property
    def sub_unique_id(self):
        """Return the unique id of the entity."""
        return "continuous_monitoring"

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
        return self._device.enable_continuous_monitoring()

    def turn_off(self):
        """Turn off continuous monitoring."""
        return self._device.disable_continuous_monitoring()


class DysonAutoModeSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson auto mode switch."""

    @property
    def sub_name(self):
        """Return the name of the entity."""
        return "Auto Mode"

    @property
    def sub_unique_id(self):
        """Return the unique id of the entity."""
        return "auto_mode"

    @property
    def icon(self):
        """Return the icon of the entity."""
        return "mdi:fan-auto"

    @property
    def is_on(self):
        """Return if auto mode is on."""
        return self._device.auto_mode

    def turn_on(self):
        """Turn on auto mode."""
        return self._device.enable_auto_mode()

    def turn_off(self):
        """Turn off auto mode."""
        return self._device.disable_auto_mode()


class DysonFrontAirflowSwitchEntity(DysonEntity, SwitchEntity):
    """Dyson fan front airflow."""

    @property
    def sub_name(self):
        """Return the name of the entity."""
        return "Front Airflow"

    @property
    def sub_unique_id(self):
        """Return the unique id of the entity."""
        return "front_airflow"

    @property
    def icon(self):
        """Return the icon of the entity."""
        return "mdi:tailwind"

    @property
    def is_on(self):
        """Return if front airflow is on."""
        return self._device.front_airflow

    def turn_on(self):
        """Turn on front airflow."""
        return self._device.enable_front_airflow()

    def turn_off(self):
        """Turn off front airflow."""
        return self._device.disable_front_airflow()
