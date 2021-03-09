from custom_components.dyson_local.fan import SERVICE_SET_TIMER, ATTR_TIMER, SERVICE_SET_ANGLE, ATTR_ANGLE_LOW, ATTR_ANGLE_HIGH
from unittest.mock import MagicMock, patch
from libdyson.const import AirQualityTarget, MessageType
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_COOL, DysonPureCool
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_COOL

ENTITY_ID = f"fan.{NAME}"

@pytest.fixture
def device() -> DysonPureCool:
    device = get_base_device(DysonPureCool, DEVICE_TYPE_PURE_COOL)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    with patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_SET_TIMER, {ATTR_TIMER: 50}, "set_sleep_timer", [50]),
        (SERVICE_SET_ANGLE, {ATTR_ANGLE_LOW: 5, ATTR_ANGLE_HIGH: 300}, "enable_oscillation", [5, 300])
    ]
)
async def test_service(hass: HomeAssistant, device: DysonPureCool, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
