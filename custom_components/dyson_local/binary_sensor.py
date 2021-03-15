"""Binary sensor platform for dyson."""

from typing import Callable

from libdyson import Dyson360Heurist

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_BATTERY_CHARGING,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson binary sensor from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entities = [DysonVacuumBatteryChargingSensor(device, name)]
    if isinstance(device, Dyson360Heurist):
        entities.append(Dyson360HeuristBinFullSensor(device, name))
    async_add_entities(entities)


class DysonVacuumBatteryChargingSensor(DysonEntity, BinarySensorEntity):
    """Dyson vacuum battery charging sensor."""

    @property
    def state(self) -> bool:
        """Return the state of the sensor."""
        return self._device.is_charging

    @property
    def device_class(self) -> str:
        """Return the device class of the sensor."""
        return DEVICE_CLASS_BATTERY_CHARGING

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Battery Charging"


class Dyson360HeuristBinFullSensor(DysonEntity, BinarySensorEntity):
    """Dyson 360 Heurist bin full sensor."""

    @property
    def state(self) -> bool:
        """Return if the bin is full."""
        return self._device.is_bin_full

    @property
    def icon(self) -> str:
        """Return the sensor icon."""
        return "mdi:delete-variant"

    @property
    def sub_name(self) -> str:
        """Return the name of the sensor."""
        return "Bin Full"
