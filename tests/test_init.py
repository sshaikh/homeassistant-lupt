"""Test component setup."""
from homeassistant.setup import async_setup_component
from london_unified_prayer_times import query as lupt_query

from custom_components.lupt.const import (
    DOMAIN,
    STATE_ATTR_LAST_UPDATED,
    STATE_ATTR_MAX_DATE,
    STATE_ATTR_MIN_DATE,
    STATE_ATTR_NUM_DATES,
)


async def test_async_setup(hass, lupt_mock_good_load):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True


async def test_async_setup_no_load(hass, lupt_mock_bad_load):
    """Test the component gets setup when no existing timetable."""
    assert await async_setup_component(hass, DOMAIN, {}) is True


def test_simple_properties(lupt_mock):
    """Test an already loaded timetable."""
    assert lupt_mock.name == "London Unified Prayer Times"
    assert lupt_mock.state == "Hello world!"


def test_extra_state_attributes(three_day_timetable, lupt_mock):
    """Test extra state attrs."""
    assert lupt_mock.extra_state_attributes == {
        STATE_ATTR_LAST_UPDATED: lupt_query.get_info(three_day_timetable)[3][
            0
        ].isoformat(),
        STATE_ATTR_MIN_DATE: "2021-10-01",
        STATE_ATTR_MAX_DATE: "2021-10-03",
        STATE_ATTR_NUM_DATES: 3,
    }
