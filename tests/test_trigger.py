"""Test the lupt trigger automation."""

from datetime import timedelta
from unittest.mock import patch

import homeassistant.components.automation as automation
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
import homeassistant.core as ha
from homeassistant.core import HassJob, callback
from homeassistant.setup import async_setup_component

from custom_components.lupt.trigger import LuptListener

from .test_init import create_utc_datetime


def help_test_next_time(hass, event, delta, dt, expected):
    """Help test next time."""
    listener = LuptListener(hass, None, event, delta)
    next_time = listener.calculate_next_time(dt)
    assert next_time == expected


def test_calculate_next_time(hass, lupt_mock):
    """Test next time."""
    help_test_next_time(
        hass,
        "Zuhr Begins",
        timedelta(),
        create_utc_datetime(2021, 10, 2, 11, 30),
        create_utc_datetime(2021, 10, 2, 11, 55),
    )

    help_test_next_time(
        hass,
        "Zuhr Begins",
        timedelta(minutes=30),
        create_utc_datetime(2021, 10, 2, 11, 30),
        create_utc_datetime(2021, 10, 2, 12, 25),
    )

    help_test_next_time(
        hass,
        "Zuhr Begins",
        timedelta(minutes=-30),
        create_utc_datetime(2021, 10, 2, 11, 00),
        create_utc_datetime(2021, 10, 2, 11, 25),
    )

    help_test_next_time(
        hass,
        "Zuhr Begins",
        timedelta(minutes=-30),
        create_utc_datetime(2021, 10, 2, 11, 26),
        create_utc_datetime(2021, 10, 3, 11, 24),
    )

    help_test_next_time(
        hass,
        "Sunrise",
        timedelta(days=1),
        create_utc_datetime(2021, 10, 2, 5, 58),
        create_utc_datetime(2021, 10, 3, 6, 00),
    )

    help_test_next_time(
        hass,
        "Sunrise",
        timedelta(days=-1),
        create_utc_datetime(2021, 10, 1, 6, 0),
        create_utc_datetime(2021, 10, 2, 6, 2),
    )


async def async_fire_time(hass, patched_time):
    """Simulate a time change."""
    with patch(
        "homeassistant.helpers.condition.dt_util.utcnow", return_value=patched_time
    ):
        hass.bus.async_fire(ha.EVENT_TIME_CHANGED, {ha.ATTR_NOW: patched_time})
        await hass.async_block_till_done()


async def test_track_event(hass, legacy_patchable_time, lupt_mock):
    """Track a lupt event."""
    utc_now = create_utc_datetime(2021, 10, 2, 5, 0)

    runs = []
    offset_runs = []
    offset = timedelta(minutes=-30)
    with patch("homeassistant.util.dt.utcnow", return_value=utc_now):
        listener = LuptListener(
            hass, HassJob(callback(lambda: runs.append(1))), "Sunrise", timedelta()
        )
        listener.async_attach()
        off_listener = LuptListener(
            hass, HassJob(callback(lambda: offset_runs.append(1))), "Sunrise", offset
        )
        off_listener.async_attach()

    await async_fire_time(hass, create_utc_datetime(2021, 10, 2, 5, 25))
    assert len(runs) == 0
    assert len(offset_runs) == 0

    await async_fire_time(hass, create_utc_datetime(2021, 10, 2, 5, 35))
    assert len(runs) == 0
    assert len(offset_runs) == 1

    await async_fire_time(hass, create_utc_datetime(2021, 10, 2, 6, 0))
    assert len(runs) == 1
    assert len(offset_runs) == 1

    off_listener.async_detach()

    await async_fire_time(hass, create_utc_datetime(2021, 10, 3, 5, 50))
    assert len(runs) == 1
    assert len(offset_runs) == 1

    listener.async_detach()

    await async_fire_time(hass, create_utc_datetime(2021, 10, 3, 7, 5))
    assert len(runs) == 1
    assert len(offset_runs) == 1


async def test_event_trigger(hass, calls, legacy_patchable_time, lupt_mock):
    """Test the event trigger."""
    now = create_utc_datetime(2021, 10, 2, 3, 0)
    trigger_time = create_utc_datetime(2021, 10, 2, 9, 0)

    with patch("homeassistant.util.dt.utcnow", return_value=now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"platform": "lupt", "event": "Fajr Begins"},
                    "action": {
                        "service": "test.automation",
                        "data_template": {"id": "{{ trigger.id}}"},
                    },
                }
            },
        )

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )

    await async_fire_time(hass, trigger_time)
    await hass.async_block_till_done()
    assert len(calls) == 0

    with patch("homeassistant.util.dt.utcnow", return_value=now):
        await hass.services.async_call(
            automation.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
            blocking=True,
        )

    await async_fire_time(hass, trigger_time)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["id"] == 0


async def test_event_trigger_with_offset(hass, calls, legacy_patchable_time, lupt_mock):
    """Test the event trigger with offset."""
    now = create_utc_datetime(2021, 10, 2, 3, 0)
    trigger_time = create_utc_datetime(2021, 10, 2, 9, 0)

    with patch("homeassistant.util.dt.utcnow", return_value=now):
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {
                        "platform": "lupt",
                        "event": "Fajr Jamā'ah",
                        "offset": "0:30:00",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.%s }}"
                            % "}} - {{ trigger.".join(("platform", "event", "offset"))
                        },
                    },
                }
            },
        )

    await async_fire_time(hass, trigger_time)
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[0].data["some"] == "lupt - Fajr Jamā'ah - 0:30:00"
