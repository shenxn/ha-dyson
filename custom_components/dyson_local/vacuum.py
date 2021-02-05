"""Vacuum platform for Dyson."""

from typing import Callable, List
from homeassistant.const import STATE_PAUSED
from libdyson.dyson_360_eye import Dyson360EyeState, Dyson360EyePowerMode
from homeassistant.components.vacuum import ATTR_STATUS, STATE_CLEANING, STATE_DOCKED, STATE_ERROR, STATE_RETURNING, SUPPORT_BATTERY, SUPPORT_FAN_SPEED, SUPPORT_PAUSE, SUPPORT_RETURN_HOME, SUPPORT_START, SUPPORT_STATE, SUPPORT_STATUS, SUPPORT_TURN_ON, StateVacuumEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import DysonEntity
from .const import DATA_DEVICES, DOMAIN

SUPPORT_360_EYE = (
    SUPPORT_START
    | SUPPORT_PAUSE
    | SUPPORT_RETURN_HOME
    | SUPPORT_FAN_SPEED
    | SUPPORT_STATUS
    | SUPPORT_STATE
    | SUPPORT_BATTERY
)

DYSON_STATUS = {
    Dyson360EyeState.INACTIVE_CHARGING: "Stopped - Charging",
    Dyson360EyeState.INACTIVE_CHARGED: "Stopped - Charged",
    Dyson360EyeState.FULL_CLEAN_PAUSED: "Paused",
    Dyson360EyeState.FULL_CLEAN_RUNNING: "Cleaning",
    Dyson360EyeState.FULL_CLEAN_ABORTED: "Returning home",
    Dyson360EyeState.FULL_CLEAN_INITIATED: "Start cleaning",
    Dyson360EyeState.FULL_CLEAN_FINISHED: "Finished",
    Dyson360EyeState.FULL_CLEAN_NEEDS_CHARGE: "Need charging",
    Dyson360EyeState.FULL_CLEAN_CHARGING: "Charging",
    Dyson360EyeState.FAULT_USER_RECOVERABLE: "Error - device blocked",
    Dyson360EyeState.FAULT_REPLACE_ON_DOCK: "Error - Replace device on dock",
}

DYSON_STATES = {
    Dyson360EyeState.INACTIVE_CHARGING: STATE_DOCKED,
    Dyson360EyeState.INACTIVE_CHARGED: STATE_DOCKED,
    Dyson360EyeState.FULL_CLEAN_PAUSED: STATE_PAUSED,
    Dyson360EyeState.FULL_CLEAN_RUNNING: STATE_CLEANING,
    Dyson360EyeState.FULL_CLEAN_ABORTED: STATE_RETURNING,
    Dyson360EyeState.FULL_CLEAN_INITIATED: STATE_CLEANING,
    Dyson360EyeState.FULL_CLEAN_FINISHED: STATE_DOCKED,
    Dyson360EyeState.FULL_CLEAN_NEEDS_CHARGE: STATE_RETURNING,
    Dyson360EyeState.FULL_CLEAN_CHARGING: STATE_PAUSED,
    Dyson360EyeState.FAULT_USER_RECOVERABLE: STATE_ERROR,
    Dyson360EyeState.FAULT_REPLACE_ON_DOCK: STATE_ERROR,
}

ATTR_POSITION = "position"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
) -> None:
    """Set up Dyson vacuum from a config entry."""
    device = hass.data[DOMAIN][DATA_DEVICES][config_entry.entry_id]
    entity = Dyson360EyeEntity(device)
    async_add_entities([entity])


class Dyson360EyeEntity(DysonEntity, StateVacuumEntity):
    """Dyson 360 Eye robot vacuum entity."""

    @property
    def state(self) -> str:
        return DYSON_STATES[self._device.state]

    @property
    def status(self) -> str:
        return DYSON_STATUS[self._device.state]

    @property
    def battery_level(self) -> int:
        """Return the battery level of the vacuum cleaner."""
        return self._device.battery_level
    @property
    def fan_speed(self) -> str:
        """Return the fan speed of the vacuum cleaner."""
        fan_speed = (
            "Max" if self._device.power_mode == Dyson360EyePowerMode.MAX
            else "Quiet"
        )
        return fan_speed

    @property
    def fan_speed_list(self) -> List[str]:
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return ["Quiet", "Max"]
    @property
    def device_state_attributes(self) -> dict:
        """Return the specific state attributes of this vacuum cleaner."""
        return {ATTR_POSITION: str(self._device.position)}

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.is_connected

    @property
    def supported_features(self) -> int:
        """Flag vacuum cleaner robot features that are supported."""
        return SUPPORT_360_EYE

    @property
    def device_state_attributes(self) -> dict:
        """Expose the status to state attributes."""
        return {ATTR_STATUS: self.status}

    def start(self) -> None:
        self._device.start()

    def pause(self) -> None:
        self._device.pause()

    def return_to_base(self, **kwargs) -> None:
        self._device.abort()

    def set_fan_speed(self, fan_speed: str, **kwargs) -> None:
        """Set fan speed."""
        power_mode = (
            Dyson360EyePowerMode.MAX if fan_speed == "Max"
            else Dyson360EyePowerMode.QUIET
        )
        self._device.set_power_mode(power_mode)
