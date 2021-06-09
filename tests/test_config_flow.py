"""Tests for the config flow."""

import pytest

from custom_components.lupt import config_flow
from custom_components.lupt.const import CONFIG_SCHEMA, DOMAIN, URL


async def test_flow_user_init(hass):
    """Test the init of the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert result["data_schema"] == CONFIG_SCHEMA
    assert result["handler"] == DOMAIN
    assert result["step_id"] == "user"
    assert result["type"] == "form"


DEFAULT_URL = "http://mock.url.com"


def build_data(url, zawaal, date_strat, mithl):
    """Build test config."""
    return {
        "url": url,
        "zawaal_mins": zawaal,
        "islamic_date_at_maghrib": date_strat,
        "use_asr_mithl_2": mithl,
    }


async def test_valid_url(hass, config_flow_good_remote):
    """Test validate_url with a good url."""
    result = await config_flow.validate_url(hass, DEFAULT_URL, None)
    assert result == DEFAULT_URL


async def test_invalid_url(hass, config_flow_bad_remote):
    """Test validate_url with a bad url."""
    with pytest.raises(config_flow.UrlValueError):
        await config_flow.validate_url(hass, "duff-url", None)


async def test_bad_url(hass):
    """Test errors produced when url is invalid."""
    _result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    bad_url = "duff-url"
    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"], user_input={URL: bad_url}
    )

    assert result["errors"] == {"base": "cannot_connect"}
