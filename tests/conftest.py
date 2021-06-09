"""Fixtures for tests."""
import datetime

from homeassistant.core import callback
from london_unified_prayer_times import config as lupt_config, timetable
import pytest
import pytz

from custom_components.lupt import Lupt, set_cached_timetable


@pytest.fixture
def three_unsorted_days():
    """Sample data with which to build a valid timetable."""
    return [
        {
            "Gregorian date": "03/10/2021",
            "Islamic day": "26",
            "Islamic month": "Safar",
            "Islamic year": "1443",
            "Sunrise": "7:02",
            "Fajr Begins": "5:34",
            "Fajr Jamā'ah": "5:54",
            "Zuhr Begins": "12:54",
            "Zuhr Jamā'ah": "1:30",
            "Asr Mithl 1": "3:53",
            "Asr Mithl 2": "4:39",
            "Asr Jamā'ah": "5:00",
            "Maghrib Begins": "6:36",
            "Maghrib Jamā'ah": "6:43",
            "Ishā Begins": "7:55",
            "Ishā Jamā'ah": "8:15",
        },
        {
            "Gregorian date": "02/10/2021",
            "Islamic day": "25",
            "Islamic month": "Safar",
            "Islamic year": "1443",
            "Sunrise": "7:00",
            "Fajr Begins": "5:32",
            "Fajr Jamā'ah": "5:52",
            "Zuhr Begins": "12:55",
            "Zuhr Jamā'ah": "1:30",
            "Asr Mithl 1": "3:54",
            "Asr Mithl 2": "4:41",
            "Asr Jamā'ah": "5:00",
            "Maghrib Begins": "6:39",
            "Maghrib Jamā'ah": "6:46",
            "Ishā Begins": "7:57",
            "Ishā Jamā'ah": "8:15",
        },
        {
            "Gregorian date": "01/10/2021",
            "Islamic day": "24",
            "Islamic month": "Safar",
            "Islamic year": "1443",
            "Sunrise": "6:58",
            "Fajr Begins": "5:30",
            "Fajr Jamā'ah": "5:50",
            "Zuhr Begins": "12:55",
            "Zuhr Jamā'ah": "1:45",
            "Asr Mithl 1": "3:56",
            "Asr Mithl 2": "4:43",
            "Asr Jamā'ah": "5:00",
            "Maghrib Begins": "6:41",
            "Maghrib Jamā'ah": "6:48",
            "Ishā Begins": "7:59",
            "Ishā Jamā'ah": "8:15",
        },
    ]


@pytest.fixture
def three_day_timetable(three_unsorted_days):
    """Create a mocked timetable."""
    prayers_config = lupt_config.default_config()
    return timetable.build_timetable(
        "pytest", "conftest.py", prayers_config, three_unsorted_days
    )


@pytest.fixture
def three_day_timetable_later(three_unsorted_days):
    """Create a mocked timetable."""
    prayers_config = lupt_config.default_config()
    return timetable.build_timetable(
        "pytest", "conftest.py", prayers_config, three_unsorted_days
    )


URL = "https://mock.location.com"


@pytest.fixture
def config():
    """Create a mocked hass config."""
    return {
        "lupt": {
            "url": URL,
            "zawaal_mins": 10,
            "islamic_date_at_maghrib": False,
            "use_asr_mithl_2": False,
        }
    }


@pytest.fixture
def start_dt():
    """Create a simple UTC time."""
    return pytz.utc.localize(datetime.datetime(2021, 10, 2, 13, 00))


@pytest.fixture
def lupt_mock_good_load(three_day_timetable, start_dt, mocker):
    """Mock lupt functions."""
    mocker.patch(
        "custom_components.lupt.lupt_cache." + "init_timetable",
        return_value=three_day_timetable,
    )
    mocker.patch("custom_components.lupt.dt_util.utcnow", return_value=start_dt)


@pytest.fixture
def lupt_mock_bad_load(three_day_timetable, start_dt, mocker):
    """Mock lupt functions."""
    mocker.patch(
        "custom_components.lupt.lupt_cache." + "init_timetable",
        side_effect=Exception,
    )
    mocker.patch(
        "custom_components.lupt.lupt_cache." + "refresh_timetable_by_name",
        return_value=three_day_timetable,
    )
    mocker.patch("custom_components.lupt.dt_util.utcnow", return_value=start_dt)


@pytest.fixture
def lupt_mock(hass, three_day_timetable, config, mocker):
    """Mock the loaded timetable."""
    lupt = Lupt(hass, config)
    set_cached_timetable(three_day_timetable)
    return lupt


@pytest.fixture
def lupt_mock_maghrib(hass, three_day_timetable, config, mocker):
    """Mock the loaded timetable."""
    config["lupt"]["islamic_date_at_maghrib"] = True
    lupt = Lupt(hass, config)
    set_cached_timetable(three_day_timetable)
    return lupt


@pytest.fixture
def lupt_mock_mithl2(hass, three_day_timetable, config, mocker):
    """Mock the loaded timetable."""
    config["lupt"]["use_asr_mithl_2"] = True
    lupt = Lupt(hass, config)
    set_cached_timetable(three_day_timetable)
    return lupt


@pytest.fixture
def calls(hass):
    """Set up a fake service & return a calls log list to this service."""
    calls = []

    @callback
    def mock_service_log(call):
        """Mock service call."""
        calls.append(call)

    hass.services.async_register("test", "automation", mock_service_log, schema=None)

    return calls


@pytest.fixture
def config_flow_good_remote(three_day_timetable, mocker):
    """Mock lupt functions."""
    mocker.patch(
        "custom_components.lupt.config_flow.remote_data." + "get_html_data",
        return_value={},
    )
    mocker.patch(
        "custom_components.lupt.config_flow.timetable." + "build_timetable",
        return_value=three_day_timetable,
    )


@pytest.fixture
def config_flow_bad_remote(three_day_timetable, mocker):
    """Mock lupt functions."""
    mocker.patch(
        "custom_components.lupt.config_flow.remote_data." + "get_html_data",
        side_effect=Exception,
    )


@pytest.fixture
def config_flow_bad_validate(mocker):
    """Mock a bad validation."""
    mocker.patch(
        "custom_components.lupt.config_flow.validate_url",
        side_effect=ValueError,
    )
