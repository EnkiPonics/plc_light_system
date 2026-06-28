# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Sensor platform for LoopingPilot. (Phase 4 – Stub)"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LoopingPilot sensor entities."""
    # Phase 4: Status-Entities implementieren
    # - sensor.loopingpilot_last_sync
    # - binary_sensor.loopingpilot_connected
