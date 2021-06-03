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
    ASR_MITHL_1_LABEL,
    ASR_MITHL_2_LABEL,
    CONFIG_SCHEMA,
    DOMAIN,
    DUHA_STATE_LABEL,
    ENTITY_ID,
    HASS_TIMETABLE,
    ISLAMIC_DATE_STRATEGY,
    MAGHRIB_TIME_LABEL,
    NAME,
    STATE_ATTR_ISLAMIC_DATE,
    STATE_ATTR_ISLAMIC_DAY,
    STATE_ATTR_ISLAMIC_MONTH,
    STATE_ATTR_ISLAMIC_YEAR,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
    SUNRISE_TIME_LABEL,
    URL,
    USE_ASR_MITHL_2,
    ZAWAAL_MINS,
    ZAWAAL_TIME_LABEL,
    IslamicDateStrategy,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the London Unified Prayer Times component."""
    lupt = Lupt(hass, config)
    await lupt.async_init()
    return True


class Lupt(Entity):
    """London Unified Prayer Times."""

    entity_id = ENTITY_ID

    def __init__(self, hass, config):
        """Initialise lupt."""
        self.hass = hass
        self.url = config[DOMAIN][URL]
        self.zawaal_delta = timedelta(minutes=config[DOMAIN][ZAWAAL_MINS])
        self.islamic_date_strategy = (
            IslamicDateStrategy.AT_MAGHRIB
            if config[DOMAIN][ISLAMIC_DATE_STRATEGY]
            else IslamicDateStrategy.AT_MIDNIGHT
        )
        self.timetable = None
        self._state = None
        self._attrs = {}
        self.config = lupt_config.default_config()

        if config[DOMAIN][USE_ASR_MITHL_2]:
            self.config[lupt_constants.ConfigKeys.DEFAULT_TIMES] = [
                ASR_MITHL_2_LABEL if x == ASR_MITHL_1_LABEL else x
                for x in self.config[lupt_constants.ConfigKeys.DEFAULT_TIMES]
            ]

        self.times = self.config[lupt_constants.ConfigKeys.DEFAULT_TIMES]
        self.rs = self.config[lupt_constants.ConfigKeys.DEFAULT_REPLACE_STRINGS]
        self.unsub_timetable = None
        self.unsub_prayer_time = None
        self.unsub_islamic_date = None

    async def async_init(self):
        """Initialise async part of lupt."""
        self.execute_if_defined(self.unsub_timetable)
        await self.update_timetable()

    def execute_if_defined(self, func):
        """Help run a function."""
        if func:
            func()

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

        dt = dt_util.utcnow()
        for prayer in self.times:
            self.calculate_next_prayer_time(prayer, dt)

        self.async_write_ha_state()

        self.execute_if_defined(self.unsub_prayer_time)
        self.update_prayer_time()

        self.execute_if_defined(self.unsub_islamic_date)
        self.update_islamic_date()

        now = dt_util.now()
        tomorrow = now + timedelta(days=1)
        sod = dt_util.start_of_local_day(tomorrow)
        next_time = sod + timedelta(minutes=15)
        next_time_utc = dt_util.as_utc(next_time)

        self.execute_if_defined(self.unsub_timetable)
        self.unsub_timetable = event.async_track_point_in_utc_time(
            self.hass, self.update_timetable, next_time_utc
        )

    @callback
    def update_prayer_time(self, now=None):
        """Calculate current prayer, update state and set up next update."""
        utc_point_in_time = dt_util.utcnow()
        next_time = self.calculate_prayer_time(utc_point_in_time)
        self.async_write_ha_state()
        self.unsub_prayer_time = event.async_track_point_in_utc_time(
            self.hass, self.update_prayer_time, next_time
        )

    @callback
    def update_islamic_date(self, now=None):
        """Calculate current idate, update state and set up next update."""
        utc_point_in_time = dt_util.utcnow()
        next_time = self.calculate_islamic_date(utc_point_in_time)
        self.async_write_ha_state()
        _LOGGER.info(f"Scheduling Islamic Date update for {next_time}")
        self.unsub_islamic_date = event.async_track_point_in_utc_time(
            self.hass, self.update_islamic_date, next_time
        )

    @property
    def name(self):
        """Friendly name."""
        return NAME

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

        next_time = None
        idate = None

        if self.islamic_date_strategy == IslamicDateStrategy.AT_MAGHRIB:
            next_time = self.calculate_next_prayer_time(MAGHRIB_TIME_LABEL, dt)
            idate = next_time.date()
        else:  # IslamicDateStrategy.AT_MIDNIGHT
            next_time = dt_util.start_of_local_day(dt) + timedelta(days=1)
            idate = dt.date()

        (iyear, imonth, iday) = lupt_query.get_islamic_date(self.timetable, idate)
        self._attrs[STATE_ATTR_ISLAMIC_DATE] = f"{iday} {imonth} {iyear}"
        self._attrs[STATE_ATTR_ISLAMIC_YEAR] = iyear
        self._attrs[STATE_ATTR_ISLAMIC_MONTH] = imonth
        self._attrs[STATE_ATTR_ISLAMIC_DAY] = iday

        return next_time

    def calculate_next_prayer_time(self, prayer, dt):
        """Set up the next time for given prayer."""
        next_prayer = lupt_query.get_now_and_next(self.timetable, [prayer], dt)[1]
        formatted_prayer_time = lupt_report.perform_replace_strings(
            prayer, self.rs
        ).lower()
        next_time = next_prayer[1]
        self._attrs[f"next_{formatted_prayer_time}"] = next_time.isoformat()
        return next_time

    def calculate_prayer_time(self, dt):
        """Calculate current prayer."""
        nandn = lupt_query.get_now_and_next(self.timetable, self.times, dt)
        current_prayer = nandn[0][0]
        self._state = lupt_report.perform_replace_strings(current_prayer, self.rs)

        next_time = nandn[1][1]

        if current_prayer == SUNRISE_TIME_LABEL:
            zawaal_time = next_time - self.zawaal_delta
            if zawaal_time <= dt:
                self._state = ZAWAAL_TIME_LABEL
            else:
                self._state = DUHA_STATE_LABEL
                next_time = zawaal_time

        self.calculate_next_prayer_time(current_prayer, dt)

        return next_time
