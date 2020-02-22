from typing import Any, Dict, Optional

from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .device import WaveEntity, get_device


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, add_entities) -> bool:
    add_entities((WaveAirQuality(get_device(hass, config_entry)),))
    return True


async def async_unload_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    return True


class WaveAirQuality(WaveEntity, AirQualityEntity):
    @property
    def device_state_attributes(self) -> dict:
        return select_keys(self._state, "humidity", "pressure", "radon_long", "temperature")

    @property
    def state(self) -> Optional[str]:
        return self._state.get("radon_short")

    @property
    def particulate_matter_2_5(self) -> Optional[float]:
        return None

    @property
    def particulate_matter_10(self) -> Optional[float]:
        return None

    @property
    def carbon_dioxide(self) -> Optional[float]:
        return self._state.get("co2")

    @property
    def volatile_organic_compounds(self) -> Optional[float]:
        return self._state.get("voc")


def select_keys(d: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    new = {}
    for key in keys:
        try:
            value = d[key]
        except KeyError:
            pass
        else:
            new[key] = value

    return new
