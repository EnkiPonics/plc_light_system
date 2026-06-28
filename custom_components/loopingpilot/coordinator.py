# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""DataUpdateCoordinator for LoopingPilot."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    COMPONENT_FISH_TANK,
    COMPONENT_GREENHOUSE,
    COMPONENT_PLANT_BED,
    CONF_API_KEY,
    CONF_ENDPOINT_URL,
    CONF_FISH_TANKS,
    CONF_FT_ID,
    CONF_FT_NAME,
    CONF_GH_ID,
    CONF_GH_NAME,
    CONF_GREENHOUSES,
    CONF_INTERVAL_SECONDS,
    CONF_LOOKBACK_SECONDS,
    CONF_LOOP_NAME,
    CONF_PB_ID,
    CONF_PB_NAME,
    CONF_PLANT_BEDS,
    CONF_SENSOR_MAPPING,
    DEFAULT_INTERVAL_SECONDS,
    DEFAULT_LOOKBACK_SECONDS,
    DOMAIN,
)
from .outbound import post_feed
from .recorder import fetch_history

_LOGGER = logging.getLogger(__name__)


class LoopingPilotCoordinator(DataUpdateCoordinator):
    """Koordiniert den zyklischen Datenabruf und (ab Phase 4) Feed-Versand."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        effective = {**entry.data, **entry.options}
        interval: int = effective.get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS)
        loop_name: str = effective.get(CONF_LOOP_NAME, entry.entry_id)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}[{loop_name}]",
            update_interval=timedelta(seconds=interval),
        )
        self._entry = entry

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _effective(self) -> dict:
        """entry.data mit entry.options überschreiben (Options Flow hat Vorrang)."""
        return {**self._entry.data, **self._entry.options}

    def _all_entity_ids(self, mapping: dict) -> list[str]:
        ids: list[str] = []
        for role_map in mapping.values():
            for entity_id in role_map.values():
                if entity_id:
                    ids.append(entity_id)
        return list(set(ids))

    def _component_list(self, config: dict) -> list[dict]:
        components: list[dict] = []
        for ft in config.get(CONF_FISH_TANKS, []):
            components.append({
                "id": ft[CONF_FT_ID],
                "name": ft[CONF_FT_NAME],
                "type": COMPONENT_FISH_TANK,
            })
        for pb in config.get(CONF_PLANT_BEDS, []):
            components.append({
                "id": pb[CONF_PB_ID],
                "name": pb[CONF_PB_NAME],
                "type": COMPONENT_PLANT_BED,
            })
        for gh in config.get(CONF_GREENHOUSES, []):
            components.append({
                "id": gh[CONF_GH_ID],
                "name": gh[CONF_GH_NAME],
                "type": COMPONENT_GREENHOUSE,
            })
        return components

    # ------------------------------------------------------------------
    # Update cycle
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        config = self._effective()
        loop_name: str = config.get(CONF_LOOP_NAME, self._entry.entry_id)
        lookback: int = config.get(CONF_LOOKBACK_SECONDS, DEFAULT_LOOKBACK_SECONDS)
        sensor_mapping: dict = config.get(CONF_SENSOR_MAPPING, {})

        entity_ids = self._all_entity_ids(sensor_mapping)

        try:
            history = await fetch_history(self.hass, entity_ids, lookback)
        except Exception as exc:
            raise UpdateFailed(f"Recorder-Abfrage fehlgeschlagen: {exc}") from exc

        components: list[dict] = []
        for comp in self._component_list(config):
            role_map: dict = sensor_mapping.get(comp["id"], {})
            measurements: dict[str, list] = {
                role: history.get(entity_id, [])
                for role, entity_id in role_map.items()
                if entity_id
            }
            components.append({
                "id": comp["id"],
                "name": comp["name"],
                "type": comp["type"],
                "measurements": measurements,
            })

        payload: dict[str, Any] = {
            "loop_name": loop_name,
            "sent_at": dt_util.utcnow().isoformat(),
            "lookback_seconds": lookback,
            "components": components,
        }

        total_points = sum(
            len(pts)
            for comp in components
            for pts in comp["measurements"].values()
        )
        _LOGGER.debug(
            "Payload assembliert: loop=%s, Komponenten=%d, Messpunkte=%d",
            loop_name,
            len(components),
            total_points,
        )

        endpoint_url: str = config.get(CONF_ENDPOINT_URL, "")
        api_key: str = config.get(CONF_API_KEY, "")
        if endpoint_url:
            session = async_get_clientsession(self.hass)
            try:
                receipt_id = await post_feed(session, endpoint_url, api_key, payload)
                _LOGGER.info(
                    "Feed gesendet: loop=%s receipt_id=%s",
                    loop_name,
                    receipt_id,
                )
                payload["last_receipt_id"] = receipt_id
            except Exception as exc:  # noqa: BLE001
                _LOGGER.warning(
                    "Feed konnte nicht gesendet werden (loop=%s): %s",
                    loop_name,
                    exc,
                )

        return payload
