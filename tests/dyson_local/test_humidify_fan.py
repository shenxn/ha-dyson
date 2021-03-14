"""Tests for Dyson fan entity of Pure Humidify+Cool."""

from unittest.mock import patch

from libdyson import (
    DEVICE_TYPE_PURE_HUMIDIFY_COOL,
    DysonPureHumidifyCool,
    HumidifyOscillationMode,
)
from libdyson.const import MessageType
import pytest

from custom_components.dyson_local import DOMAIN
from custom_components.dyson_local.fan import (
    ATTR_OSCILLATION_MODE,
    SERVICE_SET_OSCILLATION_MODE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from . import MODULE, NAME, get_base_device, update_device

ENTITY_ID = f"fan.{NAME}"


@pytest.fixture
def device() -> DysonPureHumidifyCool:
    """Return mocked device."""
    device = get_base_device(DysonPureHumidifyCool, DEVICE_TYPE_PURE_HUMIDIFY_COOL)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.oscillation_mode = HumidifyOscillationMode.BREEZE
    with patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureHumidifyCool):
    """Test entity state and attributes."""
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_OSCILLATION_MODE] == "breeze"
    device.oscillation_mode = HumidifyOscillationMode.DEGREE_45
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_OSCILLATION_MODE] == "45"
    device.oscillation_mode = HumidifyOscillationMode.DEGREE_90
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_OSCILLATION_MODE] == "90"


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (
            SERVICE_SET_OSCILLATION_MODE,
            {ATTR_OSCILLATION_MODE: "45"},
            "enable_oscillation",
            [HumidifyOscillationMode.DEGREE_45],
        ),
        (
            SERVICE_SET_OSCILLATION_MODE,
            {ATTR_OSCILLATION_MODE: "90"},
            "enable_oscillation",
            [HumidifyOscillationMode.DEGREE_90],
        ),
        (
            SERVICE_SET_OSCILLATION_MODE,
            {ATTR_OSCILLATION_MODE: "breeze"},
            "enable_oscillation",
            [HumidifyOscillationMode.BREEZE],
        ),
    ],
)
async def test_service(
    hass: HomeAssistant,
    device: DysonPureHumidifyCool,
    service: str,
    service_data: dict,
    command: str,
    command_args: list,
):
    """Test custom services."""
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
