"""Test component setup."""
import datetime
from datetime import timedelta
from unittest.mock import patch

import homeassistant.core as ha
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util
from london_unified_prayer_times import query as lupt_query
import pytz

from custom_components.lupt.const import (
    DOMAIN,
    ENTITY_ID,
    STATE_ATTR_ISLAMIC_DATE,
    STATE_ATTR_ISLAMIC_DAY,
    STATE_ATTR_ISLAMIC_MONTH,
    STATE_ATTR_ISLAMIC_YEAR,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
)

dt_util.set_default_time_zone(pytz.timezone("Europe/London"))


def create_utc_datetime(y, m, d, hh, mm):
    """Create a simple UTC time."""
    return pytz.utc.localize(datetime.datetime(y, m, d, hh, mm))


def create_local_datetime(y, m, d, hh, mm):
    """Create a simple UK time."""
    uktz = pytz.timezone("Europe/London")
    return datetime.datetime(y, m, d, hh, mm).astimezone(uktz)


async def test_async_setup(hass, lupt_mock_good_load, config):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, config) is True


async def test_async_setup_no_load(hass, lupt_mock_bad_load, config):
    """Test the component gets setup when no existing timetable."""
    assert await async_setup_component(hass, DOMAIN, config) is True


def test_simple_properties(lupt_mock):
    """Test an already loaded timetable."""
    assert lupt_mock.name == "London Unified Prayer Times"


def help_test_calc_state(lupt, dt, state, next_change):
    """Help match UTC with expected prayer state."""
    next_change_res = lupt.calculate_prayer_time(dt)
    assert lupt.state == state
    assert next_change_res == next_change


def test_calc_state(lupt_mock):
    """Test prayer state."""
    help_test_calc_state(
        lupt_mock,
        create_utc_datetime(2021, 10, 2, 13, 0),
        "Zuhr",
        create_utc_datetime(2021, 10, 2, 14, 54),
    )
    help_test_calc_state(
        lupt_mock,
        create_utc_datetime(2021, 10, 2, 16, 0),
        "Asr",
        create_utc_datetime(2021, 10, 2, 17, 39),
    )
    help_test_calc_state(
        lupt_mock,
        create_utc_datetime(2021, 10, 2, 7, 15),
        "Sunrise",
        create_utc_datetime(2021, 10, 2, 11, 45),
    )
    help_test_calc_state(
        lupt_mock,
        create_utc_datetime(2021, 10, 2, 11, 50),
        "Zawaal",
        create_utc_datetime(2021, 10, 2, 11, 55),
    )


def help_test_calc_attrs(lupt, f, attrs, next_change):
    """Help match UTC with expected prayer attrs."""
    change = f()
    for (k, v) in attrs.items():
        assert lupt.extra_state_attributes[k] == v
    assert change == next_change


def test_calculate_stats(lupt_mock):
    """Test statistics."""
    help_test_calc_attrs(
        lupt_mock,
        lupt_mock.calculate_stats,
        {
            STATE_ATTR_LAST_UPDATED: lupt_query.get_info(lupt_mock.timetable)[3][
                0
            ].isoformat(),
            STATE_ATTR_MIN_DATE: "2021-10-01",
            STATE_ATTR_MAX_DATE: "2021-10-03",
            STATE_ATTR_NUM_DATES: 3,
        },
        None,
    )


def test_calculate_islamic_date_change_on_midnight(lupt_mock):
    """Test Islamic Date."""
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_islamic_date(
            create_utc_datetime(2021, 10, 2, 13, 0)
        ),
        {
            STATE_ATTR_ISLAMIC_DATE: "25 Safar 1443",
            STATE_ATTR_ISLAMIC_YEAR: 1443,
            STATE_ATTR_ISLAMIC_MONTH: "Safar",
            STATE_ATTR_ISLAMIC_DAY: 25,
        },
        create_utc_datetime(2021, 10, 2, 23, 0),
    )
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_islamic_date(
            create_utc_datetime(2021, 10, 3, 3, 0)
        ),
        {
            STATE_ATTR_ISLAMIC_DATE: "26 Safar 1443",
            STATE_ATTR_ISLAMIC_YEAR: 1443,
            STATE_ATTR_ISLAMIC_MONTH: "Safar",
            STATE_ATTR_ISLAMIC_DAY: 26,
        },
        create_utc_datetime(2021, 10, 3, 23, 0),
    )


def test_calculate_islamic_date_change_on_maghrib(lupt_mock_maghrib):
    """Test Islamic Date changing on Maghrib."""
    help_test_calc_attrs(
        lupt_mock_maghrib,
        lambda: lupt_mock_maghrib.calculate_islamic_date(
            create_utc_datetime(2021, 10, 2, 12, 0)
        ),
        {
            STATE_ATTR_ISLAMIC_DATE: "25 Safar 1443",
            STATE_ATTR_ISLAMIC_YEAR: 1443,
            STATE_ATTR_ISLAMIC_MONTH: "Safar",
            STATE_ATTR_ISLAMIC_DAY: 25,
        },
        create_utc_datetime(2021, 10, 2, 17, 39),
    )
    help_test_calc_attrs(
        lupt_mock_maghrib,
        lambda: lupt_mock_maghrib.calculate_islamic_date(
            create_utc_datetime(2021, 10, 2, 22, 0)
        ),
        {
            STATE_ATTR_ISLAMIC_DATE: "26 Safar 1443",
            STATE_ATTR_ISLAMIC_YEAR: 1443,
            STATE_ATTR_ISLAMIC_MONTH: "Safar",
            STATE_ATTR_ISLAMIC_DAY: 26,
        },
        create_utc_datetime(2021, 10, 3, 17, 36),
    )


def test_calculate_next_prayer_time(lupt_mock):
    """Test extra state attrs."""
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_next_prayer_time(
            "Zuhr Begins", create_utc_datetime(2021, 10, 2, 13, 0)
        ),
        {"next_zuhr": create_utc_datetime(2021, 10, 3, 11, 54).isoformat()},
        create_utc_datetime(2021, 10, 3, 11, 54),
    )


def assert_state(hass, state):
    """Help assert hass state."""
    assert hass.states.get(ENTITY_ID).state == state


async def test_state_change(hass, legacy_patchable_time, lupt_mock_good_load, config):
    """Test state updates on prayer time."""
    utc_now = create_utc_datetime(2021, 10, 2, 12, 00)
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    assert_state(hass, "Zuhr")

    test_time = dt_util.parse_datetime(
        hass.states.get(ENTITY_ID).attributes["next_asr"]
    )

    assert test_time is not None

    patched_time = test_time + timedelta(seconds=5)

    with patch(
        "homeassistant.helpers.condition.dt_util.utcnow", return_value=patched_time
    ):
        hass.bus.async_fire(ha.EVENT_TIME_CHANGED, {ha.ATTR_NOW: patched_time})
        await hass.async_block_till_done()

    assert_state(hass, "Asr")


def assert_attribute(hass, attribute, value):
    """Help assert hass attrs."""
    assert hass.states.get(ENTITY_ID).attributes[attribute] == value


async def test_midnight_refresh(
    hass,
    mocker,
    legacy_patchable_time,
    three_day_timetable,
    three_day_timetable_later,
    lupt_mock_good_load,
    config,
):
    """Test timetable daily refresh."""
    utc_now = create_local_datetime(2021, 10, 2, 23, 00)
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()
    first_update = lupt_query.get_info(three_day_timetable)[3][0].isoformat()
    later_update = lupt_query.get_info(three_day_timetable_later)[3][0].isoformat()
    assert first_update != later_update
    assert_attribute(hass, STATE_ATTR_LAST_UPDATED, first_update)

    mocker.patch(
        "custom_components.lupt.lupt_cache." + "init_timetable",
        return_value=three_day_timetable_later,
    )

    patched_time = create_local_datetime(2021, 10, 3, 0, 15) + timedelta(seconds=5)

    with patch(
        "homeassistant.helpers.condition.dt_util.utcnow", return_value=patched_time
    ):
        hass.bus.async_fire(ha.EVENT_TIME_CHANGED, {ha.ATTR_NOW: patched_time})
        await hass.async_block_till_done()

    assert_attribute(hass, STATE_ATTR_LAST_UPDATED, later_update)


async def test_idate_change(hass, legacy_patchable_time, lupt_mock_good_load, config):
    """Test Islmaic date change."""
    utc_now = create_utc_datetime(2021, 10, 2, 12, 00)
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done()

    assert_attribute(hass, STATE_ATTR_ISLAMIC_DATE, "25 Safar 1443")

    patched_time = create_local_datetime(2021, 10, 3, 0, 0)
    patched_time = patched_time + timedelta(seconds=5)

    with patch(
        "homeassistant.helpers.condition.dt_util.utcnow", return_value=patched_time
    ):
        hass.bus.async_fire(ha.EVENT_TIME_CHANGED, {ha.ATTR_NOW: patched_time})
        await hass.async_block_till_done()

    assert_attribute(hass, STATE_ATTR_ISLAMIC_DATE, "26 Safar 1443")
