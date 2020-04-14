import asyncio
import datetime
import json
import logging
import time
from typing import Callable, Optional

from homeassistant.components.mqtt import Message
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType

logger = logging.getLogger(__name__)


class WaveDevice:
    __timer_handle: Optional[asyncio.TimerHandle]

    def __init__(self, hass: HomeAssistantType, device_info: dict, wave_id: str) -> None:
        self.hass = hass
        self.device_info = device_info
        self.wave_id = wave_id

        self.__state = {}
        self.__update_listeners = []

    def __str__(self) -> str:
        return f"<Wave {self.wave_id}>"

    @property
    def state(self) -> dict:
        return self.__state

    async def __handle_sample(self, msg: Message) -> None:
        try:
            payload = json.loads(msg.payload)
        except json.JSONDecodeError:
            logger.exception("received invalid sample: %r", msg.payload)
            return

        self.__state.update(payload)

    async def receive_message(self, attr: str, msg: Message) -> None:
        if attr == "sample":
            await self.__handle_sample(msg)
        elif attr == "error":
            logger.error("received error for device %s", self)
        else:
            logger.warning("unknown attribute: %r", attr)

        await self.__on_state_update()

    async def __on_state_update(self) -> None:
        hass = self.hass
        state = self.__state
        task_gen = (hass.async_add_job(listener, state) for listener in self.__update_listeners)
        await asyncio.gather(*task_gen)

    def add_update_listener(self, listener: Callable) -> None:
        self.__update_listeners.append(listener)


class WaveEntity(Entity):
    _expires_at: Optional[float]

    def __init__(self, device: WaveDevice) -> None:
        self._device = device
        self._state = device.state.copy()
        self.__update_state()

        device.add_update_listener(self.on_state_update)

    @property
    def device_info(self) -> dict:
        return self._device.device_info

    @property
    def name(self) -> str:
        return f"Wave {self._device.wave_id}"

    @property
    def available(self) -> bool:
        if self._expires_at is None:
            return True

        return time.time() < self._expires_at

    @property
    def should_poll(self) -> bool:
        return False

    async def async_added_to_hass(self) -> None:
        self.async_schedule_update_ha_state()

    def __update_state(self) -> None:
        state = self._state
        try:
            expires_at = datetime.datetime.fromisoformat(state["expires_at"])
        except (KeyError, ValueError):
            self._expires_at = None
        else:
            self._expires_at = expires_at.timestamp()

    async def on_state_update(self, state: dict) -> None:
        self._state = state
        self.__update_state()
        if self.hass is not None:
            self.async_schedule_update_ha_state()
