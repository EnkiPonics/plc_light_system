# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Recorder history access for LoopingPilot."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


async def fetch_history(
    hass: HomeAssistant,
    entity_ids: list[str],
    lookback_seconds: int,
) -> dict[str, list[dict[str, Any]]]:
    """Liest den Recorder-Verlauf für die angegebenen Entity-IDs.

    Gibt zurück: {entity_id: [{"ts": float (Unix-Epoch), "value": str}]}
    Zustände "unknown" und "unavailable" werden herausgefiltert.
    """
    if not entity_ids:
        return {}

    end = dt_util.utcnow()
    start = end - timedelta(seconds=lookback_seconds)
    instance = get_instance(hass)

    def _blocking_query() -> dict[str, list[dict[str, Any]]]:
        states = get_significant_states(
            hass,
            start,
            end,
            entity_ids=entity_ids,
            significant_changes_only=True,
            minimal_response=True,
        )
        result: dict[str, list[dict[str, Any]]] = {}
        for entity_id, state_list in states.items():
            result[entity_id] = [
                {"ts": s.last_changed.timestamp(), "value": s.state}
                for s in state_list
                if s.state not in ("unknown", "unavailable")
            ]
        return result

    try:
        return await instance.async_add_executor_job(_blocking_query)
    except Exception:
        _LOGGER.exception(
            "Fehler beim Lesen der Recorder-History (entities=%s)", entity_ids
        )
        return {}
