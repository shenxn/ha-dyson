from custom_components.dyson_local.fan import SERVICE_SET_OSCILLATION_MODE, ATTR_OSCILLATION_MODE
from unittest.mock import MagicMock, patch
from libdyson.const import AirQualityTarget, MessageType
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_HUMIDIFY_COOL, DysonPureHumidifyCool, HumidifyOscillationMode
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_HUMIDIFY_COOL

ENTITY_ID = f"fan.{NAME}"

@pytest.fixture
def device() -> DysonPureHumidifyCool:
    device = get_base_device(DysonPureHumidifyCool, DEVICE_TYPE_PURE_HUMIDIFY_COOL)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.oscillation_mode = HumidifyOscillationMode.BREEZE
    with patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureHumidifyCool):
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
        (SERVICE_SET_OSCILLATION_MODE, {ATTR_OSCILLATION_MODE: "45"}, "enable_oscillation", [HumidifyOscillationMode.DEGREE_45]),
        (SERVICE_SET_OSCILLATION_MODE, {ATTR_OSCILLATION_MODE: "90"}, "enable_oscillation", [HumidifyOscillationMode.DEGREE_90]),
        (SERVICE_SET_OSCILLATION_MODE, {ATTR_OSCILLATION_MODE: "breeze"}, "enable_oscillation", [HumidifyOscillationMode.BREEZE]),
    ]
)
async def test_service(hass: HomeAssistant, device: DysonPureHumidifyCool, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
