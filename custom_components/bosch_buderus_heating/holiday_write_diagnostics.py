"""Read-only, bounded reasons for rejected iCom holiday write contracts.

Temporary troubleshooting diagnostics only: never expose dates, modes, circuits,
temperature readings, private names or raw API payloads.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from .holidays import icom_write_configuration, icom_write_values
from .legacy_holidays import (
    SYSTEM_INFO_PATH,
    icom_assignments,
    icom_components,
    icom_dates,
    icom_empty,
    icom_mode,
    icom_modes,
    icom_slots,
    icom_temperature,
)
from .pointt import Resource

_MAX_SLOTS = 16


def icom_holiday_write_diagnostics(
    resources: Mapping[str, Resource],
) -> dict[str, object]:
    """Explain rejected iCom slots without performing reads or writes."""
    slots = icom_slots(resources)
    return {
        "slot_count": len(slots),
        "truncated": len(slots) > _MAX_SLOTS,
        "slots": [_slot_diagnostics(resources, slot) for slot in slots[:_MAX_SLOTS]],
    }


def _slot_diagnostics(resources: Mapping[str, Resource], slot: str) -> dict[str, object]:
    assigned = resources.get(f"{slot}/assignedTo")
    fixed = resources.get(f"{slot}/fixTemperature")
    configuration = icom_write_configuration(resources, slot)
    return {
        # Only the vendor's bounded numeric slot (hm1, hm2, ...).
        "slot": slot.rsplit("/", 1)[-1],
        "write_supported": configuration is not None,
        "rejection_reason": (
            None
            if configuration is not None
            else _rejection_reason(resources, slot)
        ),
        "assignments_present": assigned is not None,
        "assignments_has_values": assigned.has_values if assigned is not None else None,
        "assignments_values_count": len(assigned.values) if assigned is not None else None,
        "assignments_allowed_count": (
            len(assigned.metadata.allowed_values)
            if assigned is not None
            else None
        ),
        "fixed_temperature_present": fixed is not None,
    }


def _rejection_reason(resources: Mapping[str, Resource], slot: str) -> str:
    """Mirror validator gates in order; expose fixed reason codes only."""
    start = resources.get(f"{slot}/startStop")
    if start is None:
        return "missing_dates"
    if icom_dates(start) is None and not icom_empty(start):
        return "invalid_dates_or_empty_marker"

    assigned = resources.get(f"{slot}/assignedTo")
    if assigned is None:
        return "missing_assignments"
    if assigned.metadata.resource_type != "arrayData" or assigned.has_value:
        return "invalid_assignments_schema"
    if not assigned.has_values:
        return "assignments_values_field_missing"
    current_assignments = icom_assignments(assigned)
    if current_assignments is None:
        return "invalid_assignments"

    current_modes: dict[str, str | None] = {}
    for field, prefix in (("hcMode", "hc"), ("dhwMode", "dhw")):
        resource = resources.get(f"{slot}/{field}")
        current_modes[field] = icom_mode(resource)
        if current_modes[field] is None and (
            resource is not None
            or any(item.startswith(prefix) for item in current_assignments)
        ):
            return f"invalid_{field}_reading"

    fixed = resources.get(f"{slot}/fixTemperature")
    if fixed is not None and icom_temperature(fixed) is None:
        return "invalid_fixed_temperature_reading"
    current = icom_write_values(resources, slot)
    if current is None:
        return "invalid_slot_values"

    if not start.metadata.writable:
        return "dates_read_only"
    if not assigned.metadata.writable:
        return "assignments_read_only"
    allowed = icom_assignments(assigned, allowed=True)
    if allowed is None:
        return "invalid_allowed_assignments"
    if not allowed:
        return "no_allowed_assignments"
    if not set(current.assigned_to).issubset(allowed):
        return "current_assignments_not_allowed"

    heating_modes = icom_modes(resources.get(f"{slot}/hcMode"))
    hot_water_modes = icom_modes(resources.get(f"{slot}/dhwMode"))
    for prefix, current_mode, modes, name in (
        ("hc", current.heating_mode, heating_modes, "heating"),
        ("dhw", current.dhw_mode, hot_water_modes, "hot_water"),
    ):
        if any(item.startswith(prefix) for item in allowed):
            if not modes:
                return f"{name}_modes_unavailable"
            if current_mode not in modes:
                return f"{name}_current_mode_not_allowed"

    components = icom_components(resources.get(SYSTEM_INFO_PATH))
    if hidden := components.hidden_circuits:
        allowed = tuple(
            item
            for item in allowed
            if item not in hidden or item in current.assigned_to
        )
    if components.hmi800_hp_light:
        allowed = tuple(item for item in allowed if item in current.assigned_to)
        heating_modes = tuple(
            mode for mode in heating_modes if mode == current.heating_mode
        )
    if not allowed:
        return "no_assignments_after_component_rules"

    if fixed is None and any(
        mode in ("FIX_TEMP", "FIX_TEMPERATURE") for mode in heating_modes
    ):
        return "missing_fixed_temperature_resource"
    if fixed is not None and fixed.metadata.writable:
        minimum, maximum = fixed.metadata.minimum, fixed.metadata.maximum
        if (
            minimum is None
            or maximum is None
            or not math.isfinite(minimum)
            or not math.isfinite(maximum)
            or minimum > maximum
            or not fixed.metadata.step_size_valid
        ):
            return "invalid_fixed_temperature_limits"
        step = fixed.metadata.step_size
        if step is not None and (not math.isfinite(step) or step <= 0):
            return "invalid_fixed_temperature_step"

    return "unclassified_write_rejection"
