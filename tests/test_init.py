"""Test component setup."""
import datetime

from homeassistant.setup import async_setup_component
from london_unified_prayer_times import query as lupt_query
import pytz

from custom_components.lupt.const import (
    DOMAIN,
    STATE_ATTR_ISLAMIC_DATE,
    STATE_ATTR_ISLAMIC_DAY,
    STATE_ATTR_ISLAMIC_MONTH,
    STATE_ATTR_ISLAMIC_YEAR,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
)


def create_utc_datetime(y, m, d, hh, mm):
    """Create a simple UTC time."""
    return pytz.utc.localize(datetime.datetime(y, m, d, hh, mm))


async def test_async_setup(hass, lupt_mock_good_load, config):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, config) is True


async def test_async_setup_no_load(hass, lupt_mock_bad_load, config):
    """Test the component gets setup when no existing timetable."""
    assert await async_setup_component(hass, DOMAIN, config) is True


def test_simple_properties(lupt_mock):
    """Test an already loaded timetable."""
    assert lupt_mock.name == "London Unified Prayer Times"


def test_extra_state_attributes(three_day_timetable, lupt_mock):
    """Test extra state attrs."""


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


def help_test_calc_attrs(lupt, f, attrs):
    """Help match UTC with expected prayer attrs."""
    f()
    for (k, v) in attrs.items():
        assert lupt.extra_state_attributes[k] == v


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
    )


def test_calculate_islamic_date(lupt_mock):
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
    )


def test_calculate_next_prayer_time(lupt_mock):
    """Test extra state attrs."""
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_next_prayer_time(
            "Zuhr Begins", create_utc_datetime(2021, 10, 2, 13, 0)
        ),
        {"next_zuhr": create_utc_datetime(2021, 10, 3, 11, 54)},
    )
