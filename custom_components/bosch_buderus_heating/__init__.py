"""Bosch/Buderus Heating integration package."""

from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING, Any, cast

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util.hass_dict import HassKey

from .compatibility import sync_firmware_compatibility_issue
from .const import (
    CONF_GATEWAY_IDS,
    DOMAIN,
    PLATFORMS,
    polling_profile_from_options,
)
from .coordinator import BoschBuderusDataUpdateCoordinator
from .data import tokens_from_data, tokens_to_data
from .device import device_info_for_resource
from .holiday_ui import async_setup_holiday_ui
from .notifications import async_setup_notifications, async_update_notification_options
from .pointt import (
    AuthenticationError,
    AuthTokens,
    OAuthClient,
    PointTClient,
    PointTError,
    TokenManager,
)
from .pointt.transport import RateLimitBackoff
from .resource_catalog import (
    CapabilityMaturity,
    capability_maturity,
    configured_device_name,
)
from .runtime import BoschBuderusRuntimeData
from .startup_data import STARTUP_BUDGET_SECONDS, StartupSession, is_startup_entity_path

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

type BoschBuderusConfigEntry = ConfigEntry[BoschBuderusRuntimeData]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
_ACCOUNT_BACKOFFS: HassKey[dict[str, RateLimitBackoff]] = HassKey(
    f"{DOMAIN}.account_backoffs"
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Register the holiday form selector when the frontend is available."""
    await async_setup_holiday_ui(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: BoschBuderusConfigEntry
) -> bool:
    """Set up a Bosch/Buderus Heating config entry."""
    try:
        tokens = tokens_from_data(entry.data)
        selected_ids = _selected_gateway_ids(entry.data)
    except ValueError as err:
        raise ConfigEntryAuthFailed from err

    session = async_get_clientsession(hass)
    oauth_client = OAuthClient(session)

    async def persist_tokens(updated_tokens: AuthTokens) -> None:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, **tokens_to_data(updated_tokens)},
        )

    token_manager = TokenManager(oauth_client, tokens, persist_tokens)
    previous_runtime = getattr(entry, "runtime_data", None)
    startup = StartupSession(tuple(sorted(selected_ids)), options=dict(entry.options))
    if (
        isinstance(previous_runtime, BoschBuderusRuntimeData)
        and previous_runtime.startup is not None
        and previous_runtime.startup.can_resume(tuple(selected_ids), entry.options)
        and previous_runtime.token_manager.tokens == tokens
    ):
        startup = previous_runtime.startup
    if (
        isinstance(previous_runtime, BoschBuderusRuntimeData)
        and previous_runtime.startup is not None
        and previous_runtime.startup is not startup
    ):
        previous_runtime.startup.detach()

    @callback
    def startup_state_changed() -> None:
        # HA skips the integration's unload hook when reloading setup_retry.
        # Observe that explicit reset while preserving automatic retries.
        if entry.state in (ConfigEntryState.NOT_LOADED, ConfigEntryState.SETUP_ERROR):
            startup.close()

    startup.attach_state_listener(
        lambda: entry.async_on_state_change(startup_state_changed)
    )
    client = PointTClient(
        session,
        token_manager,
        metrics=(
            previous_runtime.client.metrics
            if isinstance(previous_runtime, BoschBuderusRuntimeData)
            and previous_runtime.startup is startup
            else None
        ),
        backoff=hass.data.setdefault(_ACCOUNT_BACKOFFS, {}).setdefault(
            entry.entry_id,
            previous_runtime.client.backoff
            if isinstance(previous_runtime, BoschBuderusRuntimeData)
            else RateLimitBackoff(),
        ),
    )
    # Keep the account brake even when gateway discovery prevents setup.
    entry.runtime_data = BoschBuderusRuntimeData(
        client, token_manager, (), (), startup=startup
    )

    try:
        gateways = await client.get_gateways()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except PointTError as err:
        raise ConfigEntryNotReady from err

    selected_gateways = tuple(
        gateway for gateway in gateways if gateway.gateway_id in selected_ids
    )
    if len(selected_gateways) != len(selected_ids):
        raise ConfigEntryNotReady("A configured gateway is currently unavailable")

    coordinators = tuple(
        BoschBuderusDataUpdateCoordinator(
            hass,
            client,
            gateway,
            entry,
            polling_profile_from_options(entry.options),
            startup_session=startup,
        )
        for gateway in selected_gateways
    )
    # Publish the safe, partially initialized runtime before the first refresh.
    # Home Assistant can then produce diagnostics when discovery itself keeps
    # the config entry in setup_retry.
    entry.runtime_data = BoschBuderusRuntimeData(
        client=client,
        token_manager=token_manager,
        gateways=selected_gateways,
        coordinators=coordinators,
        startup=startup,
    )
    _restore_registered_startup_paths(hass, entry)
    for coordinator in coordinators:
        await coordinator.async_load_fault_state()
        await coordinator.async_config_entry_first_refresh()

    await _async_load_startup_data(coordinators)

    sync_firmware_compatibility_issue(hass, entry, coordinators)

    _remove_unselected_gateway_entries(hass, entry, selected_ids)
    _enable_new_default_entities(hass, entry, coordinators)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _consolidate_logical_devices(hass, entry, coordinators)
    _remove_retired_entities(hass, entry, coordinators)
    entry.runtime_data.notifications = await async_setup_notifications(hass, entry)
    entry.async_on_unload(entry.add_update_listener(async_update_notification_options))
    startup.mark_setup_complete()
    entry.async_on_unload(startup.detach)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BoschBuderusConfigEntry
) -> bool:
    """Unload a Bosch/Buderus Heating config entry."""
    unloaded = bool(await hass.config_entries.async_unload_platforms(entry, PLATFORMS))
    if unloaded:
        if entry.runtime_data.startup is not None:
            entry.runtime_data.startup.close()
        for coordinator in entry.runtime_data.coordinators:
            coordinator.cancel_manual_setpoint_recovery()
        for manager in entry.runtime_data.notifications:
            await manager.async_close()
    return unloaded


async def async_remove_entry(
    hass: HomeAssistant, entry: BoschBuderusConfigEntry
) -> None:
    """Forget the memory-only account brake when its entry is deleted."""
    hass.data.get(_ACCOUNT_BACKOFFS, {}).pop(entry.entry_id, None)


def _restore_registered_startup_paths(
    hass: HomeAssistant, entry: BoschBuderusConfigEntry
) -> None:
    """Recover exact existing scalar IDs without guessing device identifiers."""
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.domain != "sensor" or entity.platform != DOMAIN:
            continue
        for coordinator in entry.runtime_data.coordinators:
            prefix = f"{coordinator.gateway.gateway_id}:"
            if entity.unique_id.startswith(prefix):
                path = "/" + entity.unique_id.removeprefix(prefix).replace(":", "/")
                if is_startup_entity_path(path):
                    coordinator.startup_data.schedule(path, 0, registered=True)


async def _async_load_startup_data(
    coordinators: tuple[BoschBuderusDataUpdateCoordinator, ...],
) -> None:
    """Give all core gateways priority, then share one short optional deadline."""
    deadline = monotonic() + STARTUP_BUDGET_SECONDS
    while monotonic() < deadline:
        attempted = False
        for coordinator in coordinators:
            remaining = deadline - monotonic()
            if remaining <= 0:
                break
            snapshots = dict(coordinator.data or {})
            if await coordinator.async_read_startup_batch(snapshots, budget=remaining):
                coordinator.data = snapshots
                attempted = True
        if not attempted:
            return
    for coordinator in coordinators:
        coordinator.startup_data.budget_expired(monotonic())


async def async_migrate_entry(
    hass: HomeAssistant, entry: BoschBuderusConfigEntry
) -> bool:
    """Migrate development-preview logical-device identifiers."""
    if entry.version > 3:
        return False
    if entry.version < 3:
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        for device in devices:
            for identifier in device.identifiers:
                legacy = cast(tuple[str, ...], identifier)
                if len(legacy) != 4 or legacy[0] != DOMAIN:
                    continue
                replacement = (DOMAIN, f"{legacy[1]}:{legacy[2]}:{legacy[3]}")
                existing = device_registry.async_get_device_by_identifier(
                    replacement, entry.entry_id
                )
                if existing is not None and existing.id != device.id:
                    for entity in er.async_entries_for_device(
                        entity_registry, device.id
                    ):
                        entity_registry.async_update_entity(
                            entity.entity_id, device_id=existing.id
                        )
                    device_registry.async_remove_device(device.id)
                else:
                    device_registry.async_update_device(
                        device.id, new_identifiers={replacement}
                    )
                break
        hass.config_entries.async_update_entry(entry, version=3)
    return True


def _selected_gateway_ids(data: Any) -> frozenset[str]:
    value = data.get(CONF_GATEWAY_IDS)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise ValueError("Config entry gateway selection is invalid")
    return frozenset(value)


def _remove_unselected_gateway_entries(
    hass: HomeAssistant,
    entry: BoschBuderusConfigEntry,
    selected_ids: frozenset[str],
) -> None:
    """Remove registry remnants for gateways deliberately deselected by the user."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.unique_id.startswith(f"{entry.entry_id}:request_metrics:"):
            continue
        gateway_id = entity.unique_id.split(":", 1)[0]
        if gateway_id not in selected_ids:
            entity_registry.async_remove(entity.entity_id)

    for device in tuple(
        dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    ):
        gateway_ids = {
            identifier[1].split(":", 1)[0]
            for identifier in device.identifiers
            if identifier[0] == DOMAIN
        }
        if gateway_ids and gateway_ids.isdisjoint(selected_ids):
            device_registry.async_remove_device(device.id)


def _consolidate_logical_devices(
    hass: HomeAssistant,
    entry: BoschBuderusConfigEntry,
    coordinators: tuple[BoschBuderusDataUpdateCoordinator, ...],
) -> None:
    """Move preview entities from logical devices onto their gateway device."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    devices = tuple(dr.async_entries_for_config_entry(device_registry, entry.entry_id))
    for coordinator in coordinators:
        gateway_id = coordinator.gateway.gateway_id
        gateway_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **device_info_for_resource(coordinator, "/gateway"),
        )
        prefixes = tuple(
            f"{gateway_id}:{kind}:"
            for kind in ("heating_circuit", "hot_water_circuit", "heat_source")
        )
        for device in devices:
            if device.id == gateway_device.id or not any(
                identifier[0] == DOMAIN
                and any(identifier[1].startswith(prefix) for prefix in prefixes)
                for identifier in device.identifiers
            ):
                continue
            for entity in er.async_entries_for_device(entity_registry, device.id):
                entity_registry.async_update_entity(
                    entity.entity_id, device_id=gateway_device.id
                )
            device_registry.async_remove_device(device.id)


def _remove_retired_entities(
    hass: HomeAssistant,
    entry: BoschBuderusConfigEntry,
    coordinators: tuple[BoschBuderusDataUpdateCoordinator, ...],
) -> None:
    """Remove preview entities that never represented a distinct scalar value."""
    retired_unique_ids: set[str] = set()
    observed_resource_paths: dict[str, str] = {}
    for coordinator in coordinators:
        gateway_id = coordinator.gateway.gateway_id
        for domain in (
            "totalConsumption",
            "chConsumption",
            "dhwConsumption",
            "coolingConsumption",
        ):
            retired_unique_ids.add(
                f"{gateway_id}:heatSources:emon:{domain}:electricity"
            )
        for resource in coordinator.resources.values():
            if capability_maturity(resource.path) is CapabilityMaturity.OBSERVED:
                semantic_path = resource.path.strip("/").replace("/", ":")
                observed_resource_paths[f"{gateway_id}:{semantic_path}"] = resource.path
            empty_name = resource.path.endswith("/name") and (
                not isinstance(resource.value, str)
                or configured_device_name(resource.value) is None
            )
            if (
                resource.metadata.resource_type == "switchProgram"
                and not resource.has_value
                and not resource.values
            ) or empty_name:
                semantic_path = resource.path.strip("/").replace("/", ":")
                retired_unique_ids.add(f"{gateway_id}:{semantic_path}")

    entity_registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.unique_id in retired_unique_ids or _is_observed_scalar_entity(
            entity.unique_id, observed_resource_paths
        ):
            entity_registry.async_remove(entity.entity_id)


def _is_observed_scalar_entity(
    unique_id: str, observed_resource_paths: dict[str, str]
) -> bool:
    """Match an observed resource's own scalar IDs, never its entire subtree."""
    if unique_id in observed_resource_paths:
        return True
    # Preview scalar IDs append one value key; nested keys use dots, not colons.
    resource_id, _, value_key = unique_id.rpartition(":")
    resource_path = observed_resource_paths.get(resource_id)
    if resource_path is None:
        return False
    # A direct child resource can share the shape of a scalar field ID. Keep
    # catalogued children even when discovery temporarily omits their values.
    return (
        capability_maturity(f"{resource_path}/{value_key}")
        is CapabilityMaturity.OBSERVED
    )


def _enable_new_default_entities(
    hass: HomeAssistant,
    entry: BoschBuderusConfigEntry,
    coordinators: tuple[BoschBuderusDataUpdateCoordinator, ...],
) -> None:
    """Enable newly promoted defaults without overriding user choices."""
    from .binary_sensor import build_binary_sensor_descriptions
    from .sensor import build_sensor_descriptions

    entity_registry = er.async_get(hass)
    for coordinator in coordinators:
        gateway_id = coordinator.gateway.gateway_id
        candidates = (
            (
                "sensor",
                build_sensor_descriptions(coordinator.resources),
            ),
            (
                "binary_sensor",
                build_binary_sensor_descriptions(coordinator.resources),
            ),
        )
        for platform, descriptions in candidates:
            for description in descriptions:
                if not description.entity_registry_enabled_default:
                    continue
                unique_id = f"{gateway_id}:{description.key}"
                entity_id = entity_registry.async_get_entity_id(
                    platform, DOMAIN, unique_id
                )
                if entity_id is None:
                    continue
                registered = entity_registry.async_get(entity_id)
                if (
                    registered is not None
                    and registered.config_entry_id == entry.entry_id
                    and registered.disabled_by is er.RegistryEntryDisabler.INTEGRATION
                ):
                    entity_registry.async_update_entity(entity_id, disabled_by=None)
