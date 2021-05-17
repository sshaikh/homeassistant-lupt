"""Main integration for lupt."""
from homeassistant import core
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from london_unified_prayer_times import (
    cache as lupt_cache,
    config as lupt_config,
    constants as lupt_constants,
    query as lupt_query,
    report as lupt_report,
)
import voluptuous as vol

from .const import (
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

CONFIG_SCHEMA = vol.Schema({vol.Required(URL): cv.url})


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the London Unified Prayer Times component."""
    url = config[URL]
    lupt = Lupt(hass)
    await lupt.async_init(url)
    return True


class Lupt(Entity):
    """London Unified Prayer Times."""

    entity_id = ENTITY_ID

    def __init__(self, hass):
        """Initialise lupt."""
        self.hass = hass
        self.timetable = None
        self._state = None
        self.next_change = None
        self._attrs = None
        self.config = lupt_config.load_config(None)
        self.times = None
        self.rs = None

    async def async_init(self, url):
        """Initialise async part of lupt."""
        try:
            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.init_timetable(HASS_TIMETABLE, url, self.config)
            )
        except Exception:
            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.refresh_timetable_by_name(HASS_TIMETABLE)
            )

        self.times = self.config[lupt_constants.ConfigKeys.DEFAULT_TIMES]
        self.rs = self.config[lupt_constants.ConfigKeys.DEFAULT_REPLACE_STRINGS]
        self.async_write_ha_state()

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

    def calculate_prayer_time(self, dt):
        """Calculate current prayer."""
        nandn = lupt_query.get_now_and_next(self.timetable, self.times, dt)
        self._state = lupt_report.perform_replace_strings(nandn[0][0], self.rs)
        self.next_change = nandn[1][1]

    def calculate_prayer_attrs(self, dt):
        """Calculate current attrs."""
        info = lupt_query.get_info(self.timetable)
        self._attrs = {
            STATE_ATTR_LAST_UPDATED: info[3][0].isoformat(),
            STATE_ATTR_MIN_DATE: info[2][1].isoformat(),
            STATE_ATTR_MAX_DATE: info[2][2].isoformat(),
            STATE_ATTR_NUM_DATES: info[2][0],
        }

        (iyear, imonth, iday) = lupt_query.get_islamic_date(self.timetable, dt.date())
        self._attrs[STATE_ATTR_ISLAMIC_DATE] = f"{iday} {imonth} {iyear}"
        self._attrs[STATE_ATTR_ISLAMIC_YEAR] = iyear
        self._attrs[STATE_ATTR_ISLAMIC_MONTH] = imonth
        self._attrs[STATE_ATTR_ISLAMIC_DAY] = iday

        for time in self.times:
            next_time = lupt_query.get_now_and_next(self.timetable, [time], dt)[1]
            formatted_time = lupt_report.perform_replace_strings(
                next_time[0], self.rs
            ).lower()
            self._attrs[f"next_{formatted_time}"] = next_time[1]
