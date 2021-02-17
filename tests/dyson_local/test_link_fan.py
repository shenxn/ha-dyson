from custom_components.dyson_local.fan import ATTR_AIR_QUALITY_TARGET, SERVICE_SET_AIR_QUALITY_TARGET
from unittest.mock import MagicMock, patch
from libdyson.const import AirQualityTarget, DEVICE_TYPE_PURE_COOL_LINK, MessageType
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_ENTITY_ID
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_COOL, DysonPureCool, DysonPureCoolLink
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_COOL

ENTITY_ID = f"fan.{NAME}"

@pytest.fixture
def device() -> DysonPureCoolLink:
    device = get_base_device(DysonPureCoolLink, DEVICE_TYPE_PURE_COOL_LINK)
    device.is_on = True
    device.speed = 5
    device.auto_mode = False
    device.oscillation = True
    device.air_quality_target = AirQualityTarget.GOOD
    with patch(f"{MODULE}._async_get_platforms", return_value=["fan"]):
        yield device


async def test_state(hass: HomeAssistant, device: DysonPureCoolLink):
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_AIR_QUALITY_TARGET] == "good"
    device.air_quality_target = AirQualityTarget.VERY_SENSITIVE
    await update_device(hass, device, MessageType.STATE)
    attributes = hass.states.get(ENTITY_ID).attributes
    assert attributes[ATTR_AIR_QUALITY_TARGET] == "very sensitive"


@pytest.mark.parametrize(
    "service,service_data,command,command_args",
    [
        (SERVICE_SET_AIR_QUALITY_TARGET, {ATTR_AIR_QUALITY_TARGET: "good"}, "set_air_quality_target", [AirQualityTarget.GOOD]),
        (SERVICE_SET_AIR_QUALITY_TARGET, {ATTR_AIR_QUALITY_TARGET: "default"}, "set_air_quality_target", [AirQualityTarget.DEFAULT]),
        (SERVICE_SET_AIR_QUALITY_TARGET, {ATTR_AIR_QUALITY_TARGET: "sensitive"}, "set_air_quality_target", [AirQualityTarget.SENSITIVE]),
        (SERVICE_SET_AIR_QUALITY_TARGET, {ATTR_AIR_QUALITY_TARGET: "very sensitive"}, "set_air_quality_target", [AirQualityTarget.VERY_SENSITIVE]),
    ]
)
async def test_service(hass: HomeAssistant, device: DysonPureCoolLink, service: str, service_data: dict, command: str, command_args: list):
    service_data[ATTR_ENTITY_ID] = ENTITY_ID
    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)
    func = getattr(device, command)
    func.assert_called_once_with(*command_args)
