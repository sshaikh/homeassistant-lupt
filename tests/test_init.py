"""Test component setup."""
import datetime
from datetime import timedelta
from unittest.mock import patch

import homeassistant.core as ha
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util
from london_unified_prayer_times import query as lupt_query
from pytest_homeassistant_custom_component.common import MockConfigEntry

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

DEFAULT_TZ = dt_util.get_time_zone("Europe/London")
dt_util.set_default_time_zone(DEFAULT_TZ)


def create_utc_datetime(y, m, d, hh, mm):
    """Create a simple UTC time."""
    return datetime.datetime(y, m, d, hh, mm).replace(tzinfo=datetime.timezone.utc)


def create_local_datetime(y, m, d, hh, mm):
    """Create a simple UK time."""
    return dt_util.as_local(datetime.datetime(y, m, d, hh, mm))


async def test_async_setup_from_config(hass, lupt_mock_good_load, config):
    """Test component set up from config."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)

    assert await async_setup_component(hass, DOMAIN, {})


async def test_async_setup_from_config_no_load(hass, lupt_mock_bad_load, config):
    """Test component set up from config."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)

    assert await async_setup_component(hass, DOMAIN, {})


def test_get_cached_timetable(lupt_mock, three_day_timetable):
    """Test timetable cache functions."""
    lupt_mock.set_cached_timetable(three_day_timetable)
    cached = lupt_mock.get_cached_timetable()
    assert cached == three_day_timetable


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
        "Duha",
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
            STATE_ATTR_LAST_UPDATED: lupt_query.get_info(
                lupt_mock.get_cached_timetable()
            )[3][0].isoformat(),
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


def test_calculate_asr_mithl_1(lupt_mock):
    """Test two types of asr."""
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 13, 00)
        ),
        {},
        create_utc_datetime(2021, 10, 2, 14, 54),
    )
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 15, 00)
        ),
        {"next_asr": create_utc_datetime(2021, 10, 3, 14, 53).isoformat()},
        create_utc_datetime(2021, 10, 2, 17, 39),
    )
    help_test_calc_attrs(
        lupt_mock,
        lambda: lupt_mock.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 16, 00)
        ),
        {"next_asr": create_utc_datetime(2021, 10, 3, 14, 53).isoformat()},
        create_utc_datetime(2021, 10, 2, 17, 39),
    )


def test_calculate_asr_mithl_2(lupt_mock_mithl2):
    """Test Asr Mithl 2 calculations."""
    help_test_calc_attrs(
        lupt_mock_mithl2,
        lambda: lupt_mock_mithl2.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 13, 00)
        ),
        {},
        create_utc_datetime(2021, 10, 2, 15, 41),
    )
    help_test_calc_attrs(
        lupt_mock_mithl2,
        lambda: lupt_mock_mithl2.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 15, 00)
        ),
        {},
        create_utc_datetime(2021, 10, 2, 15, 41),
    )
    help_test_calc_attrs(
        lupt_mock_mithl2,
        lambda: lupt_mock_mithl2.calculate_prayer_time(
            create_utc_datetime(2021, 10, 2, 16, 00)
        ),
        {"next_asr": create_utc_datetime(2021, 10, 3, 15, 39).isoformat()},
        create_utc_datetime(2021, 10, 2, 17, 39),
    )


def test_calculate_sunrise_gives_duha(lupt_mock):
    """Test post-Sunrise state."""
    help_test_calc_state(
        lupt_mock,
        create_utc_datetime(2021, 10, 2, 7, 0),
        "Duha",
        create_utc_datetime(2021, 10, 2, 11, 45),
    )


def assert_state(hass, state):
    """Help assert hass state."""
    assert hass.states.get(ENTITY_ID).state == state


async def test_state_change(hass, legacy_patchable_time, lupt_mock_good_load, config):
    """Test state updates on prayer time."""
    utc_now = create_utc_datetime(2021, 10, 2, 12, 00)

    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)

    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, {})

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
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, {})
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
    """Test Islamic date change."""
    utc_now = create_utc_datetime(2021, 10, 2, 12, 00)
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, {})
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


async def test_async_unload_entry(
    hass, legacy_patchable_time, lupt_mock_good_load, config
):
    """Test component is unloaded correctly."""

    utc_now = create_utc_datetime(2021, 10, 2, 12, 00)

    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)

    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=utc_now):
        await async_setup_component(hass, DOMAIN, {})

    await hass.async_block_till_done()
    assert_state(hass, "Zuhr")

    assert await config_entry.async_unload(hass)

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

    assert_state(hass, "Zuhr")
