import logging
from typing import Any, Dict, Optional

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import dispatcher
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, SIGNAL_NEW_DEVICE
from .device import WaveDevice, WaveEntity

logger = logging.getLogger(__name__)

PLATFORM = "air_quality"


def _get_platform_data(hass: HomeAssistantType) -> Dict[str, Any]:
    try:
        data = hass.data[DOMAIN][PLATFORM]
    except KeyError:
        data = hass.data[DOMAIN][PLATFORM] = {}

    return data


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, add_entities) -> bool:
    async def handle_discovery(device: WaveDevice) -> None:
        logger.debug("setting up air quality entity for device: %s", device)
        add_entities((WaveAirQuality(device),))

    disconnect = dispatcher.async_dispatcher_connect(hass, SIGNAL_NEW_DEVICE, handle_discovery)
    _get_platform_data(hass)[config_entry.entry_id] = disconnect
    return True


async def async_unload_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    try:
        disconnect = _get_platform_data(hass)[config_entry.entry_id]
    except KeyError:
        pass
    else:
        disconnect()

    return True


_EXCLUDE_KEYS = {"co2"}


class WaveAirQuality(WaveEntity, AirQualityEntity):
    @property
    def unique_id(self) -> str:
        return self._device.wave_id

    @property
    def device_state_attributes(self) -> dict:
        return {k: v for k, v in self._state.items() if k not in _EXCLUDE_KEYS}

    @property
    def state(self) -> Optional[int]:
        return self._state.get("short_term_radon")

    @property
    def particulate_matter_2_5(self) -> Optional[float]:
        return self._state.get("voc")

    @property
    def particulate_matter_10(self) -> Optional[float]:
        return None

    @property
    def carbon_dioxide(self) -> Optional[float]:
        return self._state.get("co2")
