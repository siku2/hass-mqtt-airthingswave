import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DOMAIN, KEY_DISCOVERER, PLATFORMS
from .discovery import DiscoveryHandler

logger = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    hass_data = hass.data[DOMAIN]
    discoverer = hass_data[KEY_DISCOVERER] = DiscoveryHandler(hass, config_entry)
    await discoverer.start()
    return True


async def async_unload_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(config_entry, platform)

    try:
        discoverer = hass.data[DOMAIN][KEY_DISCOVERER]
    except KeyError:
        pass
    else:
        await discoverer.stop()

    return True
