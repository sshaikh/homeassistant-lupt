"""Main integration for lupt."""
from datetime import timedelta
import logging

from homeassistant import core
from homeassistant.core import callback
from homeassistant.helpers import event
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util
from london_unified_prayer_times import (
    cache as lupt_cache,
    config as lupt_config,
    constants as lupt_constants,
    query as lupt_query,
    report as lupt_report,
)

from .const import (
    CONFIG_SCHEMA,
    DOMAIN,
    ENTITY_ID,
    HASS_TIMETABLE,
    STATE_ATTR_ISLAMIC_DATE,
    STATE_ATTR_ISLAMIC_DAY,
    STATE_ATTR_ISLAMIC_MONTH,
    STATE_ATTR_ISLAMIC_YEAR,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
    URL,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the London Unified Prayer Times component."""
    url = config[DOMAIN][URL]
    lupt = Lupt(hass, url)
    await lupt.async_init()
    return True


class Lupt(Entity):
    """London Unified Prayer Times."""

    entity_id = ENTITY_ID

    def __init__(self, hass, url):
        """Initialise lupt."""
        self.hass = hass
        self.url = url
        self.timetable = None
        self._state = None
        self._attrs = {}
        self.config = lupt_config.load_config(None)
        self.times = self.config[lupt_constants.ConfigKeys.DEFAULT_TIMES]
        self.rs = self.config[lupt_constants.ConfigKeys.DEFAULT_REPLACE_STRINGS]

    async def async_init(self):
        """Initialise async part of lupt."""
        dt = dt_util.utcnow()

        await self.update_timetable()

        self.calculate_islamic_date(dt)

        for prayer in self.times:
            self.calculate_next_prayer_time(prayer, dt)

        self.update_prayer_time()

    async def update_timetable(self, now=None):
        """Update timetable from remote."""
        try:
            _LOGGER.info(f"Initialising timetable from {self.url}.")
            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.init_timetable(HASS_TIMETABLE, self.url, self.config)
            )
        except Exception:
            _LOGGER.info("Error initialising timetable. Trying to load local copy.")
            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.refresh_timetable_by_name(HASS_TIMETABLE)
            )

        self.calculate_stats()
        self.async_write_ha_state()

        now = dt_util.now()
        tomorrow = now + timedelta(days=1)
        sod = dt_util.start_of_local_day(tomorrow)
        next_time = sod + timedelta(minutes=15)
        next_time_utc = dt_util.as_utc(next_time)

        event.async_track_point_in_utc_time(
            self.hass, self.update_timetable, next_time_utc
        )

    @callback
    def update_prayer_time(self, now=None):
        """Calculate current prayer, update state and set up next update."""
        utc_point_in_time = dt_util.utcnow()
        next_time = self.calculate_prayer_time(utc_point_in_time)
        self.async_write_ha_state()
        event.async_track_point_in_utc_time(
            self.hass, self.update_prayer_time, next_time
        )

    @property
    def name(self):
        """Friendly name."""
        return "London Unified Prayer Times"

    @property
    def state(self):
        """State."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Extra HomeAssistant attributes."""
        return self._attrs

    def calculate_stats(self):
        """Set up statistics."""
        info = lupt_query.get_info(self.timetable)
        self._attrs[STATE_ATTR_LAST_UPDATED] = info[3][0].isoformat()
        self._attrs[STATE_ATTR_MIN_DATE] = info[2][1].isoformat()
        self._attrs[STATE_ATTR_MAX_DATE] = info[2][2].isoformat()
        self._attrs[STATE_ATTR_NUM_DATES] = info[2][0]

    def calculate_islamic_date(self, dt):
        """Set up Islamic Date."""
        (iyear, imonth, iday) = lupt_query.get_islamic_date(self.timetable, dt.date())
        self._attrs[STATE_ATTR_ISLAMIC_DATE] = f"{iday} {imonth} {iyear}"
        self._attrs[STATE_ATTR_ISLAMIC_YEAR] = iyear
        self._attrs[STATE_ATTR_ISLAMIC_MONTH] = imonth
        self._attrs[STATE_ATTR_ISLAMIC_DAY] = iday

    def calculate_next_prayer_time(self, prayer, dt):
        """Set up the next time for given prayer."""
        next_prayer = lupt_query.get_now_and_next(self.timetable, [prayer], dt)[1]
        formatted_prayer_time = lupt_report.perform_replace_strings(
            prayer, self.rs
        ).lower()
        self._attrs[f"next_{formatted_prayer_time}"] = next_prayer[1].isoformat()

    def calculate_prayer_time(self, dt):
        """Calculate current prayer."""
        nandn = lupt_query.get_now_and_next(self.timetable, self.times, dt)
        current_prayer = nandn[0][0]
        self._state = lupt_report.perform_replace_strings(current_prayer, self.rs)

        self.calculate_next_prayer_time(current_prayer, dt)

        return nandn[1][1]
