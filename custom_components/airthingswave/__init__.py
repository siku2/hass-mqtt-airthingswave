import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DOMAIN
from .device import WaveDevice, get_device, set_device

logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    data = config_entry.data
    wave_id = data[CONF_ID]

    device_info = {"config_entry_id": config_entry.entry_id,
                   "identifiers": {(DOMAIN, wave_id)},
                   "manufacturer": "Airthings AS",
                   "name": data[CONF_NAME]}

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(**device_info)

    dev = WaveDevice(hass, device_info, wave_id)
    await dev.start()
    set_device(hass, wave_id, dev)

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, "air_quality"))
    return True


async def async_unload_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    hass.async_create_task(hass.config_entries.async_forward_entry_unload(config_entry, "air_quality"))
    await get_device(hass, config_entry).stop()
    return True
