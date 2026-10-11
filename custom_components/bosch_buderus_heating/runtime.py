"""Runtime data owned by one config entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .coordinator import BoschBuderusDataUpdateCoordinator
from .pointt import Gateway, PointTClient, TokenManager
from .startup_data import StartupSession

if TYPE_CHECKING:
    from .notifications import FaultNotifications


@dataclass(slots=True)
class BoschBuderusRuntimeData:
    """Live clients and selected gateways for one account."""

    client: PointTClient
    token_manager: TokenManager
    gateways: tuple[Gateway, ...]
    coordinators: tuple[BoschBuderusDataUpdateCoordinator, ...]
    notifications: tuple[FaultNotifications, ...] = ()
    startup: StartupSession | None = None
