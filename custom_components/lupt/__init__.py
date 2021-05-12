"""Main integration for lupt."""
from homeassistant import core
from homeassistant.helpers.entity import Entity
from london_unified_prayer_times import (
    cache as lupt_cache,
    config as lupt_config,
    query as lupt_query,
)

from .const import (
    ELM_URL,
    ENTITY_ID,
    HASS_TIMETABLE,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
)


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the London Unified Prayer Times component."""
    lupt = Lupt(hass)
    await lupt.async_init()
    return True


class Lupt(Entity):
    """London Unified Prayer Times."""

    entity_id = ENTITY_ID

    def __init__(self, hass):
        """Initialise lupt."""
        self.hass = hass
        self.timetable = None

    async def async_init(self):
        """Initialise async part of lupt."""
        try:
            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.refresh_timetable_by_name(HASS_TIMETABLE)
            )
        except Exception:
            config = lupt_config.load_config(None)

            self.timetable = await self.hass.async_add_executor_job(
                lambda: lupt_cache.init_timetable(HASS_TIMETABLE, ELM_URL, config)
            )

        self.async_write_ha_state()

    @property
    def name(self):
        """Friendly name."""
        return "London Unified Prayer Times"

    @property
    def state(self):
        """State."""
        return "Hello world!"

    @property
    def extra_state_attributes(self):
        """Extra HomeAssistant attributes."""
        info = lupt_query.get_info(self.timetable)
        return {
            STATE_ATTR_LAST_UPDATED: info[3][0].isoformat(),
            STATE_ATTR_MIN_DATE: info[2][1].isoformat(),
            STATE_ATTR_MAX_DATE: info[2][2].isoformat(),
            STATE_ATTR_NUM_DATES: info[2][0],
        }
