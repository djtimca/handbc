"""Definition and setup of the Surfline Sensors for Home Assistant."""

import logging

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    ATTR_NAME, 
    UnitOfTemperature,
    DEGREE,
    UnitOfTime
)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import NDBCUpdater

from .const import COORDINATOR, DOMAIN, ATTR_IDENTIFIERS, ATTR_MANUFACTURER, ATTR_MODEL

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "wind_direction": {
        "segment": "wind",
        "key": "direction",
        "unit_key": "direction_unit",
        "attribute_key": "direction_compass",
        "name": "Wind Direction",
        "icon": "mdi:compass",
        "device_class": None
    },
    "wind_speed": {
        "segment": "wind",
        "key": "speed",
        "unit_key": "speed_unit",
        "attribute_key": None,
        "name": "Wind Speed",
        "icon": "mdi:weather-windy-variant",
        "device_class": None
    },
    "wind_gusts": {
        "segment": "wind",
        "key": "gusts",
        "unit_key": "gusts_unit",
        "attribute_key": None,
        "name": "Wind Gusts",
        "icon": "mdi:weather-windy",
        "device_class": None
    },
    "wave_height": {
        "segment": "waves",
        "key": "height",
        "unit_key": "height_unit",
        "attribute_key": None,
        "name": "Wave Height",
        "icon": "mdi:waves",
        "device_class": None
    },
    "wave_period": {
        "segment": "waves",
        "key": "period",
        "unit_key": "period_unit",
        "attribute_key": None,
        "name": "Wave Period",
        "icon": "mdi:camera-timer",
        "device_class": None
    },
    "wave_average_period": {
        "segment": "waves",
        "key": "average_period",
        "unit_key": "average_period_unit",
        "attribute_key": None,
        "name": "Wave Average Period",
        "icon": "mdi:camera-timer",
        "device_class": None
    },
    "wave_direction": {
        "segment": "waves",
        "key": "direction",
        "unit_key": "direction_unit",
        "attribute_key": "direction_compass",
        "name": "Wave Direction",
        "icon": "mdi:compass",
        "device_class": None
    },
    "weather_pressure": {
        "segment": "weather",
        "key": "pressure",
        "unit_key": "pressure_unit",
        "attribute_key": None,
        "name": "Pressure",
        "icon": None,
        "device_class": "pressure"
    },
    "weather_air_temperature": {
        "segment": "weather",
        "key": "air_temperature",
        "unit_key": "air_temperature_unit",
        "attribute_key": None,
        "name": "Air Temperature",
        "icon": None,
        "device_class": "temperature"
    },
    "weather_water_temperature": {
        "segment": "weather",
        "key": "water_temperature",
        "unit_key": "water_temperature_unit",
        "attribute_key": None,
        "name": "Water Temperature",
        "icon": None,
        "device_class": "temperature"
    },
    "weather_dewpoint": {
        "segment": "weather",
        "key": "dewpoint",
        "unit_key": "dewpoint_unit",
        "attribute_key": None,
        "name": "Dewpoint",
        "icon": None,
        "device_class": "temperature"
    },
    "weather_visibility": {
        "segment": "weather",
        "key": "visibility",
        "unit_key": "visibility_unit",
        "attribute_key": None,
        "name": "Visibility",
        "icon": "mdi:eye",
        "device_class": None
    },
    "weather_pressure_tendency": {
        "segment": "weather",
        "key": "pressure_tendency",
        "unit_key": "pressure_tendency_unit",
        "attribute_key": None,
        "name": "Pressure Tendency",
        "icon": None,
        "device_class": "pressure"
    },
    "weather_tide": {
        "segment": "weather",
        "key": "tide",
        "unit_key": "tide_unit",
        "attribute_key": None,
        "name": "Tide",
        "icon": "mdi:waves-arrow-left",
        "device_class": None
    },
}

async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the sensor platforms."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []
    
    for sensor, values in SENSOR_TYPES.items():
        sensors.append(NDBCSensor(coordinator=coordinator, sensor=sensor, values=values))
    
    async_add_entities(sensors)

class NDBCSensor(CoordinatorEntity[NDBCUpdater], SensorEntity):
    """Defines a Surfline Wave sensor."""

    def __init__(
        self, 
        coordinator: NDBCUpdater, 
        sensor: str,
        values: dict
        ):
        """Initialize Entities."""

        super().__init__(coordinator=coordinator)

        self._name = f"{values['name']} - {coordinator.data['location']['name']}"
        self._unique_id = f"ndbc_{coordinator.station_id}_{sensor}"
        self._device_name = f"NDBC - {coordinator.data['location']['name']}"
        self._device_id = f"ndbc_{coordinator.station_id}"
        self._device_class = values["device_class"]
        self._segment = values["segment"]
        self._key = values["key"]
        self._raw_unit = coordinator.data["observation"][self._segment][values["unit_key"]]
        self._icon = values["icon"]
        self._attr_key = values["attribute_key"]
        self._attrs = {}

    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def device_class(self):
        """Return the correct device class for this entity."""
        return self._device_class

    @property
    def name(self):
        """Return the friendly name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for this entity."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the attributes."""
        self._attrs["last_update_utc"] = self.coordinator.data["observation"]["time"]["utc_time"]
        self._attrs["last_update_timestamp"] = self.coordinator.data["observation"]["time"]["unix_time"]
        
        if self._attr_key:
            self._attrs[self._attr_key] = self.coordinator.data["observation"][self._segment][self._attr_key]

        return self._attrs

    @property
    def device_info(self):
        """Define the device based on device_identifier."""
        location = self.coordinator.data["location"]

        device_name = self._device_name
        device_model = f"Latitude: {location['latitude']}, Longitude: {location['longitude']}"

        if location["elevation"]:
            device_model += f", Elevation: {location['elevation']}"

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_id)},
            ATTR_NAME: device_name,
            ATTR_MANUFACTURER: "NDBC",
            ATTR_MODEL: device_model,
        }

    @property
    def native_value(self):
        """Return the temperature."""
        return self.coordinator.data["observation"][self._segment][self._key]

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        unit = self._raw_unit

        if unit == "sec":
            unit = UnitOfTime.SECONDS
        elif unit == "degC":
            unit = UnitOfTemperature.CELSIUS
        elif unit == "degF":
            unit = UnitOfTemperature.FAHRENHEIT
        elif unit[0:3] == "deg":
            unit = DEGREE

        return unit

    async def async_update(self):
        """Update Entity."""
        await self.coordinator.async_request_refresh()
                
    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

