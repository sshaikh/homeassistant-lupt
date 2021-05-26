"""Constants for lupt."""
import homeassistant.helpers.config_validation as cv
from london_unified_prayer_times import constants as lupt_constants
import voluptuous as vol

DOMAIN = "lupt"
ENTITY_ID = "lupt.lupt"
URL = "url"
CONFIG_SCHEMA = vol.Schema({DOMAIN: {vol.Required(URL): cv.url}}, extra=vol.ALLOW_EXTRA)


tk = lupt_constants.TimetableKeys


STATE_ATTR_LAST_UPDATED = tk.LAST_UPDATED.value
STATE_ATTR_MIN_DATE = tk.MIN_DATE.value
STATE_ATTR_MAX_DATE = tk.MAX_DATE.value
STATE_ATTR_NUM_DATES = tk.NUMBER_OF_DATES.value
STATE_ATTR_ISLAMIC_DATE = "islamic_date"
STATE_ATTR_ISLAMIC_YEAR = "islamic_year"
STATE_ATTR_ISLAMIC_MONTH = "islamic_month"
STATE_ATTR_ISLAMIC_DAY = "islamic_day"


HASS_TIMETABLE = "homeassistant"
