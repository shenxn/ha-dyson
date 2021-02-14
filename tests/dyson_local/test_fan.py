from custom_components.dyson_local.fan import ATTR_AUTO_MODE, ATTR_DYSON_SPEED, ATTR_DYSON_SPEED_LIST, ATTR_NIGHT_MODE, SERVICE_SET_AUTO_MODE, SERVICE_SET_DYSON_SPEED, SPEED_LIST_DYSON, SPEED_LIST_HA
from unittest.mock import MagicMock, patch
from libdyson.const import DEVICE_TYPE_PURE_COOL_LINK
import pytest
from custom_components.dyson_local.const import CONF_CREDENTIAL, CONF_DEVICE_TYPE, CONF_SERIAL
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_NAME, STATE_ON
from homeassistant.components.fan import ATTR_OSCILLATING, ATTR_SPEED, ATTR_SPEED_LIST, SERVICE_SET_SPEED, SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, DOMAIN as FAN_DOMAIN
from tests.common import MockConfigEntry
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_COOL, DysonPureCool
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE

DEVICE_TYPE = DEVICE_TYPE_PURE_COOL

@pytest.fixture
def mocked_pure_cool():
    device = MagicMock(spec=DysonPureCool)
    device.serial = SERIAL
    device.device_type = DEVICE_TYPE
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    with patch(f"{MODULE}.get_device", return_value=device), patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


async def _async_setup_pure_cool(hass: HomeAssistant):
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERIAL: SERIAL,
            CONF_CREDENTIAL: CREDENTIAL,
            CONF_HOST: HOST,
            CONF_DEVICE_TYPE: DEVICE_TYPE,
            CONF_NAME: NAME,
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_pure_cool_state(hass: HomeAssistant, mocked_pure_cool: DysonPureCool):
    await _async_setup_pure_cool(hass)
    state = hass.states.get(f"fan.{NAME}")
    assert state.state == STATE_ON
    attributes = state.attributes
    assert attributes[ATTR_SPEED] == SPEED_MEDIUM
    assert attributes[ATTR_SPEED_LIST] == SPEED_LIST_HA
    assert attributes[ATTR_DYSON_SPEED] == 5
    assert attributes[ATTR_DYSON_SPEED_LIST] == SPEED_LIST_DYSON
    assert attributes[ATTR_AUTO_MODE] == False
    assert attributes[ATTR_OSCILLATING] == True


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
async def test_pure_cool_command(hass: HomeAssistant, mocked_pure_cool: DysonPureCool, service: str, service_data: dict, command: str, command_args: list):
    await _async_setup_pure_cool(hass)
    service_data[ATTR_ENTITY_ID] = f"fan.{NAME}"
    await hass.services.async_call(FAN_DOMAIN, service, service_data, blocking=True)
    func = getattr(mocked_pure_cool, command)
    func.assert_called_once_with(*command_args)


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_SET_DYSON_SPEED, {ATTR_DYSON_SPEED: 3}, "set_speed", [3]),
        (SERVICE_SET_AUTO_MODE, {ATTR_AUTO_MODE: True}, "enable_auto_mode", []),
        (SERVICE_SET_AUTO_MODE, {ATTR_AUTO_MODE: False}, "disable_auto_mode", []),
    ]
)
async def test_pure_cool_service(hass: HomeAssistant, mocked_pure_cool: DysonPureCool, service: str, service_data: dict, command: str, command_args: list):
    await _async_setup_pure_cool(hass)
    service_data[ATTR_ENTITY_ID] = f"fan.{NAME}"
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(mocked_pure_cool, command)
    func.assert_called_once_with(*command_args)
