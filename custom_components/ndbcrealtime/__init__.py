"""The NDBC Buoy Real-Time Data integration."""
import asyncio
import json

import voluptuous as vol
import logging

from datetime import timedelta, datetime
import pytz
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from ndbcrealtime import NDBC

from .const import DOMAIN, COORDINATOR, NDBC_API

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the NDBC component."""
    hass.data.setdefault(DOMAIN, {})

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up NDBC from a config entry."""
    polling_interval = 900

    conf = entry.data
    station_id = conf["station_id"]

    try:
        ndbc = NDBC(station_id = station_id)
        observation = await ndbc.get_data()
    except ConnectionError as error:
        _LOGGER.debug("NDBC API: %s", error)
        raise PlatformNotReady from error
        return False
    except ValueError as error:
        _LOGGER.debug("NDBC API: %s", error)
        raise ConfigEntryNotReady from error
        return False

    coordinator = NDBCUpdater(
        hass, 
        name="NDBC " + observation["location"]["name"], 
        station_id=station_id,
        polling_interval=polling_interval,
    )

    await coordinator.async_refresh()
    
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    for component in PLATFORMS:
        _LOGGER.info("Setting up platform: %s", component)
        await hass.config_entries.async_forward_entry_setup(entry, component)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class NDBCUpdater(DataUpdateCoordinator):
    """Class to manage fetching update data from the NDBC Realtime API."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        station_id: str,
        polling_interval: int,
    ):
        """Initialize the global NDBC data updater."""

        super().__init__(
            hass = hass,
            logger = _LOGGER,
            name = name,
            update_interval = timedelta(seconds=polling_interval),
        )

        self.station_id = station_id

    async def _async_update_data(self):
        """Fetch data from NDBC API."""
        
        try:
            #_LOGGER.debug("Updating the coordinator data.")
            ndbc = NDBC(station_id=self.station_id)
            observation = await ndbc.get_data()
        except ConnectionError as error:
            _LOGGER.info("NDBC API: %s", error)
            raise PlatformNotReady from error
        except ValueError as error:
            _LOGGER.info("NDBC API: %s", error)
            raise ConfigEntryNotReady from error

        return observation
