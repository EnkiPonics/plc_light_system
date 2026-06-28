# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""DataUpdateCoordinator for LoopingPilot. (Phase 3/4 – Stub)"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LoopingPilotCoordinator(DataUpdateCoordinator):
    """Koordiniert den zyklischen Datenabruf und Feed-Versand."""

    # Phase 3/4: Implementierung
    # - Recorder-History aller gemappten Entities lesen
    # - Payload pro Loop assemblieren
    # - HTTP POST an LoopingPilot senden
