import voluptuous as vol
from homeassistant.components.mqtt import DATA_MQTT
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.helpers.typing import HomeAssistantType

from .const import CONF_SEND_TO_AIRTHINGS, DEFAULT_NAME, DOMAIN

ERROR_ID_EXISTS = "id_exists"


def has_entry(hass: HomeAssistantType, wave_id: str) -> bool:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if wave_id == entry.data[CONF_ID]:
            return True

    return False


def is_mqtt_setup(hass: HomeAssistantType) -> bool:
    return DATA_MQTT in hass.data


class WaveConfigFlow(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: dict = None) -> dict:
        if not is_mqtt_setup(self.hass):
            return self.async_abort(reason="mqtt_required")

        errors = {}
        if user_input is not None:
            if not has_entry(self.hass, user_input[CONF_ID]):
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
            else:
                errors[CONF_ID] = ERROR_ID_EXISTS

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_ID): str,
                vol.Required(CONF_SEND_TO_AIRTHINGS, default=True): bool,
            }),
            errors=errors,
        )
