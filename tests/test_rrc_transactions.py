"""RRC transaction concurrency, uncertain responses and actual HTTP envelopes."""

import asyncio
from unittest.mock import AsyncMock

import aiohttp
import pytest
from aiohttp import web

from custom_components.bosch_buderus_heating.discovery import async_discover_resources
from custom_components.bosch_buderus_heating.pointt import (
    BatchItemResult,
    PointTClient,
    RequestTimeout,
    Resource,
    ResourceReference,
    ServiceUnavailable,
    WriteValidationError,
)
from custom_components.bosch_buderus_heating.rrc_programs import RrcProgramService
from tests.test_pointt_transport_and_client import serve
from tests.test_rrc import DAY, PAYLOADS, RESOURCES, SELECTION, WEEK, wire
from tests.test_rrc import environment as environment


@pytest.mark.parametrize(
    "zone", ["Europe/Berlin", "America/New_York", "Pacific/Auckland"]
)
async def test_weekly_sunday_clock_change_time_is_not_converted(environment, zone):
    coordinator, _client, _ = environment
    state = wire(environment)
    await coordinator.hass.config.async_update(time_zone=zone)
    await coordinator.async_edit_rrc_program(state[WEEK], 1, 430, 22)
    assert state[WEEK].value[-1] == {"d": "Su", "t": 150, "Th": 20}
    assert state[WEEK].value[0]["t"] == 0


async def test_single_zone_leaf_is_sufficient_to_probe_its_known_fields():
    client = AsyncMock()

    async def bulk(gateway, paths):
        return tuple(
            BatchItemResult(
                gateway,
                path,
                200,
                Resource(
                    path,
                    references=(ResourceReference("/zones/zn5/temperatureActual"),),
                ),
            )
            if path == "/zones"
            else BatchItemResult(gateway, path, 404)
            for path in paths
        )

    client.get_resources_bulk.side_effect = bulk
    await async_discover_resources(client, "fixture", roots=("/zones",))
    paths = {
        path
        for call in client.get_resources_bulk.call_args_list
        for path in call.args[1]
    }
    assert "/zones/zn5/userMode" in paths and "/programs/list" in paths
    assert not any("/zn1/" in path for path in paths)


@pytest.mark.parametrize("operation", ["select", "edit"])
async def test_applied_write_with_lost_response_is_confirmed_without_repetition(
    environment, operation
):
    coordinator, client, _ = environment
    state = wire(environment)
    original_put = client.put_resource_value.side_effect

    async def lost(*args):
        await original_put(*args)
        raise RequestTimeout("lost")

    client.put_resource_value.side_effect = lost
    if operation == "select":
        await coordinator.async_select_rrc_program(SELECTION, 7)
        assert coordinator.data[SELECTION].resource.value == 7
    else:
        await coordinator.async_edit_rrc_program(state[WEEK], 1, 430, 22)
        assert coordinator.data[WEEK].resource.value[1]["t"] == 430
    assert client.put_resource_value.await_count == 1


@pytest.mark.parametrize("operation", ["select", "edit"])
async def test_noop_checks_current_resources_but_does_not_write(environment, operation):
    coordinator, client, _ = environment
    state = wire(environment)
    if operation == "select":
        await coordinator.async_select_rrc_program(SELECTION, 3)
    else:
        await coordinator.async_edit_rrc_program(state[WEEK], 1, 425, 21.5)
    assert client.get_resource.await_count == 2
    client.put_resource_value.assert_not_awaited()


@pytest.mark.parametrize("operation", ["select", "edit"])
async def test_temporary_readback_error_is_bounded(environment, operation):
    coordinator, client, _ = environment
    state = wire(environment)
    get = client.get_resource.side_effect
    failed = False

    async def delayed(*args):
        nonlocal failed
        if client.put_resource_value.await_count and not failed:
            failed = True
            raise ServiceUnavailable(503)
        return await get(*args)

    client.get_resource.side_effect = delayed
    if operation == "select":
        await coordinator.async_select_rrc_program(SELECTION, 7)
    else:
        await coordinator.async_edit_rrc_program(state[WEEK], 1, 430, 22)
    assert client.put_resource_value.await_count == 1
    assert client.get_resource.await_count == 4


async def test_queued_schedule_edit_detects_previous_edit(environment):
    coordinator, client, _ = environment
    wire(environment)
    started, finish = asyncio.Event(), asyncio.Event()
    put = client.put_resource_value.side_effect

    async def slow(*args):
        started.set()
        await finish.wait()
        await put(*args)

    client.put_resource_value.side_effect = slow
    first = asyncio.create_task(
        coordinator.async_edit_rrc_program(RESOURCES[WEEK], 1, 430, 22)
    )
    await started.wait()
    second = asyncio.create_task(
        coordinator.async_edit_rrc_program(RESOURCES[WEEK], 1, 435, 23)
    )
    await asyncio.sleep(0)
    finish.set()
    await first
    with pytest.raises(WriteValidationError):
        await second
    assert client.put_resource_value.await_count == 1


@pytest.mark.usefixtures("socket_enabled")
async def test_real_pointt_wire_envelopes_and_paths_for_rrc():
    state = {item["id"]: dict(item) for item in PAYLOADS}
    writes = []

    async def handler(request):
        assert request.headers["Authorization"] == "Bearer synthetic"
        path = "/" + request.match_info["resource"]
        if request.method == "PUT":
            body = await request.json()
            writes.append((path, body))
            assert set(body) == {"value"}
            state[path]["value"] = body["value"]
            if path == DAY:
                state[WEEK]["value"] = body["value"] + [
                    point for point in state[WEEK]["value"] if point["d"] != "Mo"
                ]
            return web.Response(status=204)
        return web.json_response(state[path])

    route = "/gateways/fixture/resource/{resource:.*}"
    async with (
        serve([("GET", route, handler), ("PUT", route, handler)]) as url,
        aiohttp.ClientSession() as session,
    ):
        service = RrcProgramService(
            PointTClient(session, "synthetic", base_url=url), sleep=AsyncMock()
        )
        await service.select("fixture", SELECTION, 7)
        await service.edit("fixture", RESOURCES[WEEK], 1, 430, 22)
    assert writes == [
        (SELECTION, {"value": 7}),
        (
            DAY,
            {
                "value": [
                    {"d": "Mo", "t": 0, "Th": 16},
                    {"d": "Mo", "t": 430, "Th": 22},
                    {"d": "Mo", "t": 1320, "Th": 16},
                ]
            },
        ),
    ]
