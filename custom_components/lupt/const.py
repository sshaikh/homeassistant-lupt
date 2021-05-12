"""Constants for lupt."""
from london_unified_prayer_times import constants as lupt_constants

DOMAIN = "lupt"
ENTITY_ID = "lupt.lupt"

tk = lupt_constants.TimetableKeys

STATE_ATTR_LAST_UPDATED = tk.LAST_UPDATED.value
STATE_ATTR_MIN_DATE = tk.MIN_DATE.value
STATE_ATTR_MAX_DATE = tk.MAX_DATE.value
STATE_ATTR_NUM_DATES = tk.NUMBER_OF_DATES.value

HASS_TIMETABLE = "homeassistant"
ELM_URL = "https://mock.location.com"
