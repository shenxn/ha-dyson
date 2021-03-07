from typing import Type
from libdyson.dyson_device import DysonDevice, DysonFanDevice
from custom_components.dyson_local.fan import SPEED_LIST_HA, SUPPORTED_FEATURES
from unittest.mock import MagicMock, patch
from libdyson.const import AirQualityTarget, DEVICE_TYPE_PURE_COOL_LINK, MessageType
import pytest
from custom_components.dyson_local.const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_SERIAL
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.components.fan import ATTR_OSCILLATING, ATTR_SPEED, ATTR_SPEED_LIST, SERVICE_SET_SPEED, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, DOMAIN as FAN_DOMAIN, SPEED_OFF
from homeassistant.helpers import entity_registry
from tests.common import MockConfigEntry
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_COOL, DysonPureCool, DysonPureCoolLink
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_COOL

ENTITY_ID = f"fan.{NAME}"


@pytest.fixture(
    params=[
        (DysonPureCool, DEVICE_TYPE_PURE_COOL),
        (DysonPureCoolLink, DEVICE_TYPE_PURE_COOL_LINK),
    ]
)
def device(request: pytest.FixtureRequest) -> DysonFanDevice:
    device = get_base_device(request.param[0], request.param[1])
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.air_quality_target = AirQualityTarget.GOOD
    with patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonFanDevice):
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_SPEED] == SPEED_MEDIUM
    assert attributes[ATTR_SPEED_LIST] == SPEED_LIST_HA
    assert attributes[ATTR_OSCILLATING] is True
    assert attributes[ATTR_SUPPORTED_FEATURES] == SUPPORTED_FEATURES

    er = await entity_registry.async_get_registry(hass)
    assert er.async_get(ENTITY_ID).unique_id == SERIAL

    device.is_on = False
    device.speed = None
    device.auto_mode = True
    device.oscillation = False
    await update_device(hass, device, MessageType.STATE)
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    attributes = state.attributes
    assert attributes[ATTR_SPEED] is None
    assert attributes[ATTR_OSCILLATING] is False


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        ("turn_on", {}, "turn_on", []),
        ("turn_on", {ATTR_SPEED: SPEED_HIGH}, "set_speed", [10]),
        ("turn_off", {}, "turn_off", []),
        ("set_speed", {ATTR_SPEED: SPEED_LOW}, "set_speed", [4]),
        ("oscillate", {ATTR_OSCILLATING: True}, "enable_oscillation", []),
        ("oscillate", {ATTR_OSCILLATING: False}, "disable_oscillation", []),
    ]
)
async def test_command(hass: HomeAssistant, device: DysonFanDevice, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(FAN_DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
