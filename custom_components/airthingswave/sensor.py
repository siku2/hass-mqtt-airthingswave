import dataclasses
from typing import Any, Dict, List, Optional, Union

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import dispatcher
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, SIGNAL_NEW_DEVICE
from .device import WaveDevice, WaveEntity

PLATFORM = "sensor"


def _get_platform_data(hass: HomeAssistantType) -> Dict[str, Any]:
    try:
        data = hass.data[DOMAIN][PLATFORM]
    except KeyError:
        data = hass.data[DOMAIN][PLATFORM] = {}

    return data


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry, add_entities) -> bool:
    async def handle_discovery(device: WaveDevice) -> None:
        add_entities(create_sensors(device))

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


@dataclasses.dataclass()
class SensorInfo:
    id: str
    icon: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None

    def name(self) -> str:
        return self.id.replace("_", " ").title()


SENSORS = (
    SensorInfo("humidity", icon="mdi:water-percent", unit_of_measurement="%", device_class="humidity"),
    SensorInfo("light_level", icon="mdi:lightbulb", unit_of_measurement="lm", device_class="illuminance"),
    SensorInfo("short_term_radon", icon="mdi:radioactive", unit_of_measurement="Bq/m3"),
    SensorInfo("long_term_radon", icon="mdi:radioactive", unit_of_measurement="Bq/m3"),
    SensorInfo("temperature", icon="mdi:thermometer", unit_of_measurement="°C", device_class="temperature"),
    SensorInfo("pressure", icon="mdi:percent", unit_of_measurement="mbar", device_class="pressure"),
    SensorInfo("co2", icon="mdi:molecule-co2", unit_of_measurement="ppm"),
    SensorInfo("voc", icon="mdi:air-filter", unit_of_measurement="ppb"),
)


class WaveAttrSensor(WaveEntity):
    _sensor: SensorInfo

    def __init__(self, device: WaveDevice, sensor: SensorInfo) -> None:
        super().__init__(device)
        self._sensor = sensor

    @property
    def unique_id(self) -> Optional[str]:
        return f"{self._device.wave_id}-{self._sensor.id}"

    @property
    def name(self) -> str:
        return f"{super().name} {self._sensor.name()}"

    @property
    def state(self) -> Union[None, str, int, float]:
        return self._state.get(self._sensor.id)

    @property
    def device_class(self) -> Optional[str]:
        return self._sensor.device_class

    @property
    def unit_of_measurement(self) -> Optional[str]:
        return self._sensor.unit_of_measurement

    @property
    def icon(self) -> Optional[str]:
        return self._sensor.icon


def create_sensors(device: WaveDevice) -> List[WaveAttrSensor]:
    sensors = []
    for sensor in SENSORS:
        if sensor.id in device.state:
            sensors.append(WaveAttrSensor(device, sensor))

    return sensors
