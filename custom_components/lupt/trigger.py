"""Offer lupt based automation rules."""
from datetime import timedelta
import logging

from homeassistant.const import CONF_EVENT, CONF_OFFSET, CONF_PLATFORM
from homeassistant.core import HassJob, callback
from homeassistant.helpers import event
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt as dt_util
from london_unified_prayer_times import query as lupt_query
import voluptuous as vol

from .const import CACHED_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

TRIGGER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
        vol.Required(CONF_EVENT): cv.string,
        vol.Required(CONF_OFFSET, default=timedelta(0)): cv.time_period,
    }
)


async def async_attach_trigger(hass, config, action, automation_info):
    """Listen for events based on configuration."""
    trigger_id = automation_info.get("trigger_id") if automation_info else None
    event = config.get(CONF_EVENT)
    offset = config.get(CONF_OFFSET)
    description = event
    if offset:
        description = f"{description} with offset"
    job = HassJob(action)

    @callback
    def call_action():
        """Call action with right context."""
        hass.async_run_hass_job(
            job,
            {
                "trigger": {
                    "platform": DOMAIN,
                    "event": event,
                    "offset": offset,
                    "description": description,
                    "id": trigger_id,
                }
            },
        )

    listener = LuptListener(hass, HassJob(call_action), event, offset)
    listener.async_attach()
    return listener.async_detach


class LuptListener:
    """Helper class to listen to Lupt events."""

    def __init__(self, hass, job, event, offset):
        """Initialise listener."""
        _LOGGER.info("Initialising LUPT listener.")
        self.hass = hass
        self.job = job
        self.event = event
        self.offset = offset
        self._unsub = None

    def get_cached_timetable(self):
        """Retrieve cached timetable from hass."""
        return self.hass.data[DOMAIN][CACHED_KEY]

    @callback
    def async_attach(self) -> None:
        """Attach listener."""
        _LOGGER.info("Attaching listener.")
        self._listen_next_event()

    @callback
    def async_detach(self) -> None:
        """Detach listener."""
        _LOGGER.info("Detaching listener.")
        self._unsub()
        self._unsub = None

    def calculate_next_time(self, dt):
        """Calculate the next trigger time."""
        original_event_time = dt - self.offset
        nandn = lupt_query.get_now_and_next(
            self.get_cached_timetable(), [self.event], original_event_time
        )
        next_time = nandn[1][1] + self.offset
        return next_time

    @callback
    def _listen_next_event(self) -> None:
        """Set up the listener."""

        dt = dt_util.utcnow()
        next_time = self.calculate_next_time(dt)

        _LOGGER.info(f"Scheduling next event for {next_time.isoformat()}")
        self._unsub = event.async_track_point_in_utc_time(
            self.hass, self._handle_event, next_time
        )

    @callback
    def _handle_event(self, now) -> None:
        """Handle event."""
        _LOGGER.info("Triggering LUPT job.")
        self._unsub = None
        self._listen_next_event()
        self.hass.async_run_hass_job(self.job)
