from typing import Type
from libdyson.dyson_device import DysonDevice
from custom_components.dyson_local.humidifier import MIN_HUMIDITY, MAX_HUMIDITY, SUPPORTED_FEATURES, SERVICE_SET_WATER_HARDNESS, ATTR_WATER_HARDNESS
from unittest.mock import MagicMock, patch
from libdyson import DysonPureHumidifyCool, DEVICE_TYPE_PURE_HUMIDIFY_COOL, MessageType, WaterHardness
from libdyson.const import AirQualityTarget
import pytest
from custom_components.dyson_local.const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_SERIAL
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.helpers import entity_registry
from homeassistant.components.humidifier import DOMAIN as HUMIDIFIER_DOMAIN, ATTR_MODE, ATTR_HUMIDITY, SERVICE_TURN_ON, SERVICE_TURN_OFF, SERVICE_SET_HUMIDITY, SERVICE_SET_MODE
from homeassistant.components.humidifier.const import MODE_NORMAL, MODE_AUTO
from tests.common import MockConfigEntry
from custom_components.dyson_local import DOMAIN
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_HUMIDIFY_COOL

ENTITY_ID = f"humidifier.{NAME}"


@pytest.fixture
def device() -> DysonPureHumidifyCool:
    device = get_base_device(DysonPureHumidifyCool, DEVICE_TYPE_PURE_HUMIDIFY_COOL)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.air_quality_target = AirQualityTarget.GOOD
    device.humidification = True
    device.humidification_auto_mode = True
    device.humidity_target = 50
    with patch(f"{MODULE}._async_get_platforms", return_value=["humidifier"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureHumidifyCool):
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_MODE] == MODE_AUTO
    assert attributes[ATTR_HUMIDITY] == 50

    er = await entity_registry.async_get_registry(hass)
    assert er.async_get(ENTITY_ID).unique_id == SERIAL

    device.humidification_auto_mode = False
    device.humidity_target = 30
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_MODE] == MODE_NORMAL
    assert attributes[ATTR_HUMIDITY] == 30

    device.humidification = False
    await update_device(hass, device, MessageType.STATE)
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_TURN_ON, {}, "enable_humidification", []),
        (SERVICE_TURN_OFF, {}, "disable_humidification", []),
        (SERVICE_SET_HUMIDITY, {ATTR_HUMIDITY: 30}, "set_humidity_target", [30]),
        (SERVICE_SET_MODE, {ATTR_MODE: MODE_AUTO}, "enable_humidification_auto_mode", []),
        (SERVICE_SET_MODE, {ATTR_MODE: MODE_NORMAL}, "disable_humidification_auto_mode", []),
    ]
)
async def test_command(hass: HomeAssistant, device: DysonPureHumidifyCool, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(HUMIDIFIER_DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_SET_WATER_HARDNESS, {ATTR_WATER_HARDNESS: "soft"}, "set_water_hardness", [WaterHardness.SOFT]),
        (SERVICE_SET_WATER_HARDNESS, {ATTR_WATER_HARDNESS: "medium"}, "set_water_hardness", [WaterHardness.MEDIUM]),
        (SERVICE_SET_WATER_HARDNESS, {ATTR_WATER_HARDNESS: "hard"}, "set_water_hardness", [WaterHardness.HARD]),
    ]
)
async def test_service(hass: HomeAssistant, device: DysonPureHumidifyCool, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
