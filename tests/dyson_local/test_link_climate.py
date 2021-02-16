from custom_components.dyson_local.climate import FAN_MODES, HVAC_MODES, SUPPORT_FLAGS, SUPPORT_FLAGS_LINK
from typing import Type
from homeassistant.components.climate.const import ATTR_CURRENT_HUMIDITY, ATTR_CURRENT_TEMPERATURE, ATTR_FAN_MODE, ATTR_FAN_MODES, ATTR_HUMIDITY, ATTR_HVAC_ACTION, ATTR_HVAC_MODE, ATTR_HVAC_MODES, ATTR_MAX_TEMP, ATTR_MIN_TEMP, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT, CURRENT_HVAC_IDLE, CURRENT_HVAC_OFF, FAN_DIFFUSE, FAN_FOCUS, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_OFF, SERVICE_SET_FAN_MODE, SERVICE_SET_HVAC_MODE, SERVICE_SET_TEMPERATURE
from libdyson.dyson_device import DysonDevice
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from unittest.mock import MagicMock, patch
from libdyson.const import ENVIRONMENTAL_INIT, MessageType
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.helpers import entity_registry
from tests.common import MockConfigEntry
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_HOT_COOL, DEVICE_TYPE_PURE_HOT_COOL_LINK, DysonPureHotCool, DysonPureHotCoolLink
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_HOT_COOL

ENTITY_ID = f"climate.{NAME}"


@pytest.fixture(
    params=[
        (DysonPureHotCoolLink, DEVICE_TYPE_PURE_HOT_COOL_LINK),
    ]
)
def device(request: pytest.FixtureRequest) -> DysonPureHotCoolLink:
    device = get_base_device(request.param[0], request.param[1])
    device.is_on = True
    device.heat_mode_is_on = True
    device.heat_status_is_on = True
    device.heat_target = 280
    device.temperature = 275
    device.humidity = 30
    device.focus_mode = False
    with patch(f"{MODULE}._async_get_platforms", return_value=["climate"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureHotCoolLink):
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_FAN_MODE] == FAN_DIFFUSE
    assert attributes[ATTR_FAN_MODES] == FAN_MODES
    assert attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_FLAGS_LINK

    device.focus_mode = True
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_FAN_MODE] == FAN_FOCUS


@pytest.mark.parametrize(
    "service,service_data,command",
    [
        (SERVICE_SET_FAN_MODE, {ATTR_FAN_MODE: FAN_FOCUS}, "enable_focus_mode"),
        (SERVICE_SET_FAN_MODE, {ATTR_FAN_MODE: FAN_DIFFUSE}, "disable_focus_mode"),
    ]
)
async def test_command(hass: HomeAssistant, device: DysonPureHotCoolLink, service: str, service_data: dict, command: str):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(CLIMATE_DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with()
