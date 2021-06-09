"""Config flow for Lupt."""

from typing import Any, Dict, Optional

from homeassistant import config_entries, exceptions
from london_unified_prayer_times import config, constants, remote_data, timetable

from .const import CONFIG_SCHEMA, DOMAIN, HTML_CLASS, NAME, URL

DEFAULT_CONFIG = config.default_config()
DEFAULT_CSS = DEFAULT_CONFIG[constants.ConfigKeys.HTML_TABLE_CSS_CLASS]


async def validate_url(hass, url, css):
    """Validate the config provided."""
    try:
        data = await hass.async_add_executor_job(
            lambda: remote_data.get_html_data(url, css)
        )
        timetable.build_timetable("test", url, DEFAULT_CONFIG, data)
    except Exception:
        raise UrlValueError

    return url


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Lupt config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            url = user_input[URL]
            try:
                css = user_input[HTML_CLASS] or DEFAULT_CSS
                await validate_url(self.hass, url, css)
                return self.async_create_entry(title=NAME, data=user_input)
            except UrlValueError:
                print("url error")
                errors["base"] = "cannot_connect"
            except Exception:
                print("other error")
                errors["base"] = "unknown"

        print(f"returning {errors}")
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )


class UrlValueError(exceptions.HomeAssistantError):
    """Error to indicate we have a bad URL."""
