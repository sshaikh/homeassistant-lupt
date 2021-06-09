"""Constants for lupt."""
from enum import Enum

import homeassistant.helpers.config_validation as cv
from london_unified_prayer_times import constants as lupt_constants
import voluptuous as vol

NAME = "London Unified Prayer Times"
DOMAIN = "lupt"
ENTITY_ID = "lupt.lupt"
URL = "url"
HTML_CLASS = "html_table_css_class"
ZAWAAL_MINS = "zawaal_mins"
ISLAMIC_DATE_STRATEGY = "islamic_date_at_maghrib"
USE_ASR_MITHL_2 = "use_asr_mithl_2"
CACHED_KEY = "cached_timetable"

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(URL): cv.string,
        vol.Optional(HTML_CLASS, default=""): cv.string,
        vol.Required(ZAWAAL_MINS, default=10): cv.positive_int,
        vol.Required(ISLAMIC_DATE_STRATEGY, default=False): cv.boolean,
        vol.Required(USE_ASR_MITHL_2, default=False): cv.boolean,
    },
)

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

SUNRISE_TIME_LABEL = "Sunrise"
DUHA_STATE_LABEL = "Duha"
ZAWAAL_TIME_LABEL = "Zawaal"
MAGHRIB_TIME_LABEL = "Maghrib Begins"
ASR_MITHL_1_LABEL = "Asr Mithl 1"
ASR_MITHL_2_LABEL = "Asr Mithl 2"


class IslamicDateStrategy(Enum):
    """Islamic Date Strategy Options."""

    AT_MIDNIGHT = "at_midnight"
    AT_MAGHRIB = "at_maghrib"
