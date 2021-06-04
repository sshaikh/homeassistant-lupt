"""Offer lupt based automation rules."""
import logging

from homeassistant.core import callback
from homeassistant.helpers import event
from homeassistant.util import dt as dt_util
from london_unified_prayer_times import query as lupt_query

from . import get_cached_timetable

_LOGGER = logging.getLogger(__name__)


class LuptListener:
    """Helper class to listen to Lupt events."""

    def __init__(self, hass, job, prayer, offset):
        """Initialise listener."""
        _LOGGER.info("Initialising LUPT listener.")
        self.hass = hass
        self.job = job
        self.prayer = prayer
        self.offset = offset
        self._unsub = None

    @callback
    def async_attach(self) -> None:
        """Attach listener."""
        _LOGGER.info("Attaching listener.")
        self._listen_next_prayer_event()

    @callback
    def async_detach(self) -> None:
        """Detach listener."""
        _LOGGER.info("Detaching listener.")
        self._unsub()
        self._unsub = None

    def calculate_next_time(self, dt):
        """Calculate the next trigger time."""
        original_prayer_time = dt - self.offset
        nandn = lupt_query.get_now_and_next(
            get_cached_timetable(), [self.prayer], original_prayer_time
        )
        next_time = nandn[1][1] + self.offset
        return next_time

    @callback
    def _listen_next_prayer_event(self) -> None:
        """Set up the listener."""

        dt = dt_util.utcnow()
        next_time = self.calculate_next_time(dt)

        _LOGGER.info(f"Scheduling next event for {next_time.isoformat()}")
        self._unsub = event.async_track_point_in_utc_time(
            self.hass, self._handle_event, next_time
        )

    @callback
    def _handle_event(self, now) -> None:
        """Handle prayer event."""
        _LOGGER.info("Triggering LUPT job.")
        self._unsub = None
        self._listen_next_prayer_event()
        self.hass.async_run_hass_job(self.job)
