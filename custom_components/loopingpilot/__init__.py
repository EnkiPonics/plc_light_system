# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""LoopingPilot Home Assistant Adapter."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import LoopingPilotCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LoopingPilot from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = LoopingPilotCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    _LOGGER.info("LoopingPilot Adapter gestartet (entry_id=%s)", entry.entry_id)
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Eintrag bei Options-Änderung neu laden."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a LoopingPilot config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("LoopingPilot Adapter entladen (entry_id=%s)", entry.entry_id)

    return unload_ok
