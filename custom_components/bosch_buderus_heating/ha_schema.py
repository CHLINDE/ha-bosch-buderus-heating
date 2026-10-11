"""Use the form-validation backend selected by the installed Home Assistant."""

from typing import TYPE_CHECKING

__all__ = ["validation"]

if TYPE_CHECKING:
    # The pinned development HA uses Probatio. Older supported HA versions
    # still need Voluptuous markers, even when Probatio is also installed.
    import probatio as validation
else:
    from importlib import import_module

    from homeassistant.helpers import config_validation as cv

    validation = import_module(type(cv.PLATFORM_SCHEMA).__module__.partition(".")[0])
