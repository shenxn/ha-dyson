"""Air quality platform for dyson."""

from typing import Callable
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.components.air_quality import AirQualityEntity
from libdyson.const import MessageType
from libdyson.dyson_device import DysonDevice

from . import DysonEntity
from .const import DATA_COORDINATORS, DOMAIN, DATA_DEVICES

ATTR_VOC = "volatile_organic_compounds"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson air quality from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][config_entry.entry_id]
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entities = [DysonAirQualityEntity(coordinator, device, name)]
    async_add_entities(entities)


class DysonAirQualityEntity(CoordinatorEntity, DysonEntity, AirQualityEntity):

    _MESSAGE_TYPE: MessageType.ENVIRONMENTAL

    def __init__(self, coordinator: DataUpdateCoordinator, device: DysonDevice, name: str):
        CoordinatorEntity.__init__(self, coordinator)
        DysonEntity.__init__(self, device, name)

    @property
    def name(self):
        """Return the name of the air quality entity."""
        return f"{super().name} Air Quality"

    @property
    def particulate_matter_2_5(self):
        """Return the particulate matter 2.5 level."""
        return self._device.particulars

    @property
    def particulate_matter_10(self):
        """Return the particulate matter 10 level."""
        return self._device.particulars

    @property
    def volatile_organic_compounds(self):
        """Return the VOC (Volatile Organic Compounds) level."""
        return self._device.volatile_organic_compounds

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        return {ATTR_VOC: self.volatile_organic_compounds}

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return "level"
