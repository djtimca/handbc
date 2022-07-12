"""Config flow for Surfline."""
import logging
import voluptuous as vol

from homeassistant.helpers.selector import selector
from ndbcrealtime import NDBC, Stations

from homeassistant import config_entries
from homeassistant.helpers import config_entry_flow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NDBC Real Time Data."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            config_entry = self.hass.config_entries.async_entries(DOMAIN + user_input["station_id"])
            if config_entry:
                return self.async_abort(reason="single_instance_allowed")
            
            observation = {}

            try:
                ndbc = NDBC(station_id=user_input["station_id"])
                observation = await ndbc.get_data()
                
            except ValueError as error:
                _LOGGER.exception(f"Value Error: {error}")
                errors["base"] = "invalid_station_id"
            except ConnectionError as error:
                _LOGGER.exception(f"Connection Error: {error}")
                errors["base"] = "cannot_connect"
            except Exception as error:  # pylint: disable=broad-except
                _LOGGER.exception(f"Unexpected exception: {error}")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(DOMAIN + user_input["station_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="NDBC - " + observation["location"]["name"], data=user_input)

        stations = Stations()
        list = await stations.list()
        stations_list = []

        for station_id, station in list.items():
            stations_list.append({
                "label": station_id + " - " + station["@name"],
                "value": station_id
            })
        
        data_schema = {}
        data_schema["station_id"]=selector({
            "select": {
                "options": stations_list
            }
        })

        return self.async_show_form(
            step_id="user",
            data_schema = vol.Schema(data_schema),
            errors=errors,
        )
