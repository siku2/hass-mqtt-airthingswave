from homeassistant.helpers import config_entry_flow
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN


async def _async_has_devices(hass: HomeAssistantType) -> bool:
    # TODO
    return True


config_entry_flow.register_discovery_flow(DOMAIN, "MQTT", _async_has_devices)
