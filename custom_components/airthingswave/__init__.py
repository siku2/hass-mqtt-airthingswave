import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType, HomeAssistantType, ServiceCallType

from .const import DOMAIN, KEY_DISCOVERER, PLATFORMS
from .discovery import DiscoveryHandler

logger = logging.getLogger(__name__)


def _register_services(hass: HomeAssistantType) -> None:
    def send_command(method: str, **kwargs) -> None:
        payload = kwargs
        payload["method"] = method
        mqtt.async_publish(hass, "wave/command", payload)

    async def handle_discover(_call: ServiceCallType) -> None:
        send_command("discover")

    async def handle_update(call: ServiceCallType) -> None:
        send_command("update", devices=call.data.get("devices"))

    hass.services.register(DOMAIN, "discover", handle_discover)
    hass.services.register(DOMAIN, "update", handle_update)


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    hass_data = hass.data[DOMAIN]
    _register_services(hass)

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
