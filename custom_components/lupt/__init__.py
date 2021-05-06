from homeassistant import core
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util
from london_unified_prayer_times import (
    cache as lupt_cache,
    config as lupt_config,
    constants as lupt_constants,
    query as lupt_query,
)

DOMAIN = "lupt"
ENTITY_ID = "lupt.lupt"

tk = lupt_constants.TimetableKeys

STATE_ATTR_LAST_UPDATED = tk.LAST_UPDATED.value
STATE_ATTR_MIN_DATE = tk.MIN_DATE.value
STATE_ATTR_MAX_DATE = tk.MAX_DATE.value
STATE_ATTR_NUM_DATES = tk.NUMBER_OF_DATES.value

HASS_TIMETABLE = "homeassistant"
ELM_URL = "https://mock.location.com"

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the London Unified Prayer Times component."""
    # @TODO: Add setup code.
    lupt = Lupt(hass)
    await lupt.async_init()
    return True


class Lupt(Entity):
    """London Unified Prayer Times"""

    entity_id = ENTITY_ID

    def __init__(self, hass):
        """Initialise lupt."""
        self.hass = hass


    async def async_init(self):
#        try:
#            self.timetable = lupt_cache.load_timetable(HASS_TIMETABLE, None)
#        except Exception:
        config = lupt_config.load_config(None)
        self.timetable = await self.hass.async_add_executor_job(lambda: lupt_cache.init_timetable(HASS_TIMETABLE, ELM_URL, config))

        self.async_write_ha_state()



    @property
    def name(self):
        return "London Unified Prayer Times"

    @property
    def state(self):
        return "Hello world!"

    @property
    def extra_state_attributes(self):
        info = lupt_query.get_info(self.timetable)
        return {
            STATE_ATTR_LAST_UPDATED: info[3][0].isoformat(),
            STATE_ATTR_MIN_DATE: info[2][1].isoformat(),
            STATE_ATTR_MAX_DATE: info[2][2].isoformat(),
            STATE_ATTR_NUM_DATES: info[2][0]
        }
