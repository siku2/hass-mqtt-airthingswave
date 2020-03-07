import asyncio
import logging
from typing import Dict, Optional

from homeassistant.components.mqtt import Message, subscription
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import dispatcher
from homeassistant.helpers.typing import HomeAssistantType

from .const import DOMAIN, KEY_DEVICES, PLATFORMS, SIGNAL_NEW_DEVICE
from .device import WaveDevice

logger = logging.getLogger(__name__)

_SN_MODEL_MAP = {
    "2900": "Wave",
    "2920": "Wave Mini",
    "2930": "Wave Plus",
    "2950": "Wave 2nd gen",
}


def model_from_serial_number(sn: str) -> Optional[str]:
    try:
        return _SN_MODEL_MAP[sn[:4]]
    except KeyError:
        return None


class DiscoveryHandler:
    def __init__(self, hass: HomeAssistantType, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry

        self._hass_data = hass.data[DOMAIN]
        self._subscription_state = {}
        self._platforms_setup = False

        self.__device_lock = asyncio.Lock()
        self.__setup_lock = asyncio.Lock()

    @property
    def _devices(self) -> Dict[str, WaveDevice]:
        hass_data = self._hass_data
        try:
            devices = hass_data[KEY_DEVICES]
        except KeyError:
            devices = hass_data[KEY_DEVICES] = {}

        return devices

    async def start(self) -> None:
        await subscription.async_subscribe_topics(self.hass, self._subscription_state, {
            "discovery": dict(topic="wave/#", msg_callback=self.__handle_message)
        })

    async def stop(self) -> None:
        await subscription.async_unsubscribe_topics(self.hass, self._subscription_state)

    async def __handle_message(self, msg: Message) -> None:
        try:
            _, sn, attr = msg.topic.split("/", 2)
        except ValueError:
            logger.warning("received message with invalid wave topic: %s", msg)
            return

        logger.debug("received message %r for %s", attr, sn)

        async with self.__device_lock:
            try:
                device = self._devices[sn]
            except KeyError:
                device = await self.__setup_new_device(sn)

        await device.receive_message(attr, msg)

    async def __ensure_platforms_setup(self) -> None:
        async with self.__setup_lock:
            if self._platforms_setup:
                return

            for platform in PLATFORMS:
                logger.debug("setting up platform %s", platform)
                await self.hass.config_entries.async_forward_entry_setup(self.config_entry, platform)

            self._platforms_setup = True

    async def __setup_new_device(self, sn: str) -> WaveDevice:
        logger.info("discovered new device: %s", sn)
        await self.__ensure_platforms_setup()

        device_info = {"config_entry_id": self.config_entry.entry_id,
                       "identifiers": {(DOMAIN, sn)},
                       "manufacturer": "Airthings AS",
                       "model": model_from_serial_number(sn),
                       "name": f"Wave {sn}"}
        device = self._devices[sn] = WaveDevice(self.hass, device_info, sn)
        dispatcher.async_dispatcher_send(self.hass, SIGNAL_NEW_DEVICE, device)
        return device
