"""Sensor platform for dyson."""

from typing import Callable
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ICON, ATTR_NAME, ATTR_UNIT_OF_MEASUREMENT, CONF_NAME, TIME_HOURS
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import DEVICE_CLASS_BATTERY
from homeassistant.config_entries import ConfigEntry
from libdyson import DysonDevice, Dyson360Eye

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN


SENSORS = {
    "battery_level": ("Battery Level", {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY,
    }),
    "filter_life": ("Filter Life", {
        ATTR_ICON: "mdi:filter-outline",
        ATTR_UNIT_OF_MEASUREMENT: TIME_HOURS,
    })
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson sensor from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    sensors = []
    if isinstance(device, Dyson360Eye):
        sensors.append(DysonBatterySensor)
    else:
        sensors.append(DysonFilterLifeSensor)
    entities = [
        sensor(device, config_entry.data[CONF_NAME])
        for sensor in sensors
    ]
    async_add_entities(entities)


class DysonSensor(DysonEntity):
    """Generic Dyson sensor."""

    _SENSOR_TYPE = None

    def __init__(self, device: DysonDevice, name: str):
        """Initialize the sensor."""
        super().__init__(device, name)
        self._old_value = None
        self._sensor_name, self._attributes = SENSORS[self._SENSOR_TYPE]

    @property
    def name(self):
        """Return the name of the Dyson sensor."""
        return f"{super().name} {self._sensor_name}"

    @property
    def unique_id(self):
        """Return the sensor's unique id."""
        return f"{self._device.serial}-{self._SENSOR_TYPE}"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._attributes.get(ATTR_UNIT_OF_MEASUREMENT)

    @property
    def icon(self):
        """Return the icon for this sensor."""
        return self._attributes.get(ATTR_ICON)

    @property
    def device_class(self):
        """Return the device class of this sensor."""
        return self._attributes.get(ATTR_DEVICE_CLASS)


class DysonBatterySensor(DysonSensor):

    _SENSOR_TYPE = "battery_level"

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._device.battery_level


class DysonFilterLifeSensor(DysonSensor):
    """Dyson filter life sensor (in hours) for Pure Cool Link."""

    _SENSOR_TYPE = "filter_life"

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._device.filter_life
