"""Prepare PointT holiday time zones outside Home Assistant's event loop."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import tzinfo

from homeassistant.util import dt as dt_util

from .holidays import holiday_timezone_names
from .pointt import Resource


async def async_resolve_holiday_timezones(
    resources: Mapping[str, Resource],
    previous: Mapping[str, tzinfo | None],
) -> dict[str, tzinfo | None]:
    """Resolve changed names and retain only the current bounded set of zones.

    Remember invalid names too, so repeated rendering and polling cannot cause
    repeated disk lookups. Publish the complete result only after every await.
    """
    resolved: dict[str, tzinfo | None] = {}
    for name in sorted(holiday_timezone_names(resources)):
        if name in previous:
            resolved[name] = previous[name]
            continue
        try:
            resolved[name] = await dt_util.async_get_time_zone(name)
        except ValueError:
            # ZoneInfo rejects absolute paths, traversal and malformed names.
            resolved[name] = None
    return resolved
