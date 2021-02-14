from custom_components.dyson_local.sensor import SENSORS
from typing import List, Type
from homeassistant.util.unit_system import IMPERIAL_SYSTEM
from libdyson.dyson_device import DysonDevice, DysonFanDevice
from unittest.mock import MagicMock, patch
from libdyson.const import DEVICE_TYPE_360_EYE, DEVICE_TYPE_PURE_COOL_LINK, ENVIRONMENTAL_OFF, MessageType
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, ATTR_ICON, ATTR_UNIT_OF_MEASUREMENT, CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.helpers import entity_registry
from tests.common import MockConfigEntry
from custom_components.dyson_local import DOMAIN
from libdyson import DEVICE_TYPE_PURE_COOL, DysonPureCool, DysonPureCoolLink, Dyson360Eye
from . import NAME, SERIAL, CREDENTIAL, HOST, MODULE, get_base_device, name_to_entity, update_device

DEVICE_TYPE = DEVICE_TYPE_PURE_COOL


@pytest.fixture
def device(request: pytest.FixtureRequest) -> DysonDevice:
    with patch(f"{MODULE}._async_get_platforms", return_value=["sensor"]):
        yield request.param()


def _get_fan(spec: Type[DysonFanDevice], device_type: str) -> DysonFanDevice:
    device = get_base_device(spec, device_type)
    device.humidity = 50
    device.temperature = 280
    return device


def _get_pure_cool_link() -> DysonPureCoolLink:
    device = _get_fan(DysonPureCoolLink, DEVICE_TYPE_PURE_COOL_LINK)
    device.filter_life = 200
    return device


def _get_pure_cool_combined() -> DysonPureCool:
    device = _get_fan(DysonPureCool, DEVICE_TYPE_PURE_COOL)
    device.carbon_filter_life = None
    device.hepa_filter_life = 50
    return device


def _get_pure_cool_seperated() -> DysonPureCool:
    device = _get_fan(DysonPureCool, DEVICE_TYPE_PURE_COOL)
    device.carbon_filter_life = 30
    device.hepa_filter_life = 50
    return device


def _get_360_eye() -> Dyson360Eye:
    device = get_base_device(Dyson360Eye, DEVICE_TYPE_360_EYE)
    device.battery_level = 80
    return device


@pytest.mark.parametrize(
    "device,sensors",
    [
        (_get_pure_cool_link, ["humidity", "temperature", "filter_life"]),
        (_get_pure_cool_combined, ["humidity", "temperature", "combined_filter_life"]),
        (_get_pure_cool_seperated, ["humidity", "temperature", "carbon_filter_life", "hepa_filter_life"]),
        (_get_360_eye, ["battery_level"]),
    ],
    indirect=["device"]
)
async def test_sensors(
    hass: HomeAssistant,
    device: DysonFanDevice,
    sensors: List[str],
):
    er = await entity_registry.async_get_registry(hass)
    assert len(hass.states.async_all()) == len(sensors)
    for sensor in sensors:
        name, attributes = SENSORS[sensor]
        entity_id = f"sensor.{NAME}_{name_to_entity(name)}"
        state = hass.states.get(entity_id)
        assert state.name == f"{NAME} {name}"
        for attr, value in attributes.items():
            assert state.attributes[attr] == value
        assert er.async_get(entity_id).unique_id == f"{SERIAL}-{sensor}"


@pytest.mark.parametrize(
    "device", [_get_pure_cool_link, _get_pure_cool_combined], indirect=True
)
async def test_fan(hass: HomeAssistant, device: DysonFanDevice):
    assert hass.states.get(f"sensor.{NAME}_humidity").state == "50"
    state = hass.states.get(f"sensor.{NAME}_temperature")
    assert state.state == "6.9"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == TEMP_CELSIUS

    device.humidity = 30
    device.temperature = 300
    hass.config.units = IMPERIAL_SYSTEM
    await update_device(hass, device, MessageType.ENVIRONMENTAL)
    assert hass.states.get(f"sensor.{NAME}_humidity").state == "30"
    state = hass.states.get(f"sensor.{NAME}_temperature")
    assert state.state == "80.3"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == TEMP_FAHRENHEIT

    device.temperature = ENVIRONMENTAL_OFF
    await update_device(hass, device, MessageType.ENVIRONMENTAL)
    assert hass.states.get(f"sensor.{NAME}_temperature").state == STATE_OFF


@pytest.mark.parametrize(
    "device", [_get_pure_cool_link], indirect=True
)
async def test_pure_cool_link(hass: HomeAssistant, device: DysonFanDevice):
    assert hass.states.get(f"sensor.{NAME}_filter_life").state == "200"
    device.filter_life = 100
    await update_device(hass, device, MessageType.STATE)
    assert hass.states.get(f"sensor.{NAME}_filter_life").state == "100"


@pytest.mark.parametrize(
    "device", [_get_pure_cool_combined], indirect=True
)
async def test_pure_cool_combined(hass: HomeAssistant, device: DysonFanDevice):
    assert hass.states.get(f"sensor.{NAME}_filter_life").state == "50"
    device.hepa_filter_life = 30
    await update_device(hass, device, MessageType.STATE)
    assert hass.states.get(f"sensor.{NAME}_filter_life").state == "30"


@pytest.mark.parametrize(
    "device", [_get_pure_cool_seperated], indirect=True
)
async def test_pure_cool_combined(hass: HomeAssistant, device: DysonFanDevice):
    assert hass.states.get(f"sensor.{NAME}_carbon_filter_life").state == "30"
    assert hass.states.get(f"sensor.{NAME}_hepa_filter_life").state == "50"
    device.carbon_filter_life = 20
    device.hepa_filter_life = 30
    await update_device(hass, device, MessageType.STATE)
    assert hass.states.get(f"sensor.{NAME}_carbon_filter_life").state == "20"
    assert hass.states.get(f"sensor.{NAME}_hepa_filter_life").state == "30"


@pytest.mark.parametrize(
    "device", [_get_360_eye], indirect=True
)
async def test_360_eye(hass: HomeAssistant, device: DysonFanDevice):
    assert hass.states.get(f"sensor.{NAME}_battery_level").state == "80"
    device.battery_level = 40
    await update_device(hass, device, MessageType.STATE)
    assert hass.states.get(f"sensor.{NAME}_battery_level").state == "40"
