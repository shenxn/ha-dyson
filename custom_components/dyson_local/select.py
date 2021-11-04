"""Select platform for dyson."""

from typing import Callable, Union

from libdyson import DysonPureHumidifyCool, WaterHardness

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, ENTITY_CATEGORY_CONFIG
from homeassistant.core import HomeAssistant

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN


WATER_HARDNESS_STR_TO_ENUM = {
    "Soft": WaterHardness.SOFT,
    "Medium": WaterHardness.MEDIUM,
    "Hard": WaterHardness.HARD,
}

WATER_HARDNESS_ENUM_TO_STR = {
    value: key for key, value in WATER_HARDNESS_STR_TO_ENUM.items()
}


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson select from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    name = config_entry.data[CONF_NAME]
    entities = []
    if isinstance(device, DysonPureHumidifyCool):
        entities.append(DysonWaterHardnessSelect(device, name))
    async_add_entities(entities)


class DysonWaterHardnessSelect(DysonEntity, SelectEntity):
    """Dyson Pure Humidify+Cool Water Hardness Select."""

    _attr_entity_category = ENTITY_CATEGORY_CONFIG
    _attr_icon = "mdi:water-opacity"
    _attr_options = list(WATER_HARDNESS_STR_TO_ENUM.keys())

    @property
    def current_option(self) -> str:
        return WATER_HARDNESS_ENUM_TO_STR[self._device.water_hardness]

    def select_option(self, option: str) -> None:
        self._device.set_water_hardness(WATER_HARDNESS_STR_TO_ENUM[option])

    @property
    def sub_name(self) -> str:
        """Return the name of the select."""
        return "Water Hardness"

    @property
    def sub_unique_id(self):
        """Return the select's unique id."""
        return "water_hardness"
