import asyncio
import logging
from typing import Callable, Optional

from homeassistant.components.mqtt import Message, subscription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType

from custom_components.airthingswave.const import WAVE_DEVICES

logger = logging.getLogger(__name__)

WAVE_ATTRS = ("online", "humidity", "temperature", "light", "co2", "voc", "radon_short", "radon_long", "pressure")


class WaveDevice:
    __timer_handle: Optional[asyncio.TimerHandle]

    def __init__(self, hass: HomeAssistantType, device_info: dict, wave_id: str) -> None:
        self.hass = hass
        self.device_info = device_info
        self.wave_id = wave_id
        self.debounce_delay = 5

        self.__sub_state = {}
        self.__state = {}
        self.__timer_handle = None
        self.__update_listeners = []

    @property
    def state(self) -> dict:
        return self.__state

    def __handle_message(self, msg: Message) -> None:
        _, _, attr = msg.topic.rpartition("/")
        self.__state[attr] = msg.payload

        if self.__timer_handle is not None:
            return

        self.__timer_handle = self.hass.loop.call_later(self.debounce_delay, self.__handle_state_update)

    def __handle_state_update(self) -> None:
        self.__timer_handle = None
        asyncio.create_task(self.__on_state_update())

    async def __on_state_update(self) -> None:
        state = self.__state
        for listener in self.__update_listeners:
            await listener(state)

    async def _subscribe(self) -> None:
        topics = {}
        prefix = f"wave/{self.wave_id}/"
        for attr in WAVE_ATTRS:
            topic = prefix + attr
            topics[attr] = dict(topic=topic, msg_callback=self.__handle_message)

        self.__sub_state = await subscription.async_subscribe_topics(
            self.hass,
            self.__sub_state,
            topics,
        )

    async def _unsubscribe(self) -> None:
        self.__sub_state = await subscription.async_unsubscribe_topics(self.hass, self.__sub_state)

    async def start(self) -> None:
        await self._subscribe()

    async def stop(self) -> None:
        await self._unsubscribe()
        if self.__timer_handle is not None:
            self.__timer_handle.cancel()
            self.__timer_handle = None

    def add_update_listener(self, listener: Callable) -> None:
        self.__update_listeners.append(listener)


def get_device(hass: HomeAssistantType, config_entry: ConfigEntry) -> WaveDevice:
    wave_id = config_entry.data[CONF_ID]
    return hass.data[WAVE_DEVICES][wave_id]


def set_device(hass: HomeAssistantType, wave_id: str, device: WaveDevice) -> None:
    hass_data = hass.data
    try:
        devices = hass_data[WAVE_DEVICES]
    except KeyError:
        devices = hass_data[WAVE_DEVICES] = {}

    devices[wave_id] = device


class WaveEntity(Entity):
    def __init__(self, device: WaveDevice) -> None:
        self._device = device
        self._state = {}

        device.add_update_listener(self.on_state_update)

    @property
    def device_info(self) -> dict:
        return self._device.device_info

    @property
    def available(self) -> bool:
        try:
            online = self._device.state["online"]
        except KeyError:
            return False

        return online == "ON"

    @property
    def name(self) -> str:
        return self._device.wave_id

    @property
    def should_poll(self) -> bool:
        return False

    async def on_state_update(self, state: dict) -> None:
        self._state = state
        self.async_schedule_update_ha_state()
