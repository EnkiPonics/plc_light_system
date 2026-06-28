# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Options flow for LoopingPilot – Sensor-Mapping und Verbindung nachträglich ändern."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    AQUAPONIC_SENSOR_ROLES,
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
    CONF_PB_ID,
    CONF_PB_MEDIUM,
    CONF_PB_NAME,
    CONF_PLANT_BEDS,
    CONF_SENSOR_MAPPING,
    DEFAULT_INTERVAL_SECONDS,
    DEFAULT_LOOKBACK_SECONDS,
    ENVIRONMENT_SENSOR_ROLES,
    PLANT_BED_ROLES_BY_MEDIUM,
    SENSOR_TYPE_NAME,
)


class LoopingPilotOptionsFlow(config_entries.OptionsFlow):
    """Sensor-Mapping und Verbindungseinstellungen nachträglich ändern."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry
        self._sensor_mapping: dict[str, dict[str, str | None]] = {}
        self._mapping_queue: list[dict] = []
        self._mapping_idx: int = 0

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        self._build_mapping_queue()
        current: dict = {
            **self._entry.data.get(CONF_SENSOR_MAPPING, {}),
            **self._entry.options.get(CONF_SENSOR_MAPPING, {}),
        }
        self._sensor_mapping = {k: dict(v) for k, v in current.items()}
        return await self.async_step_sensor_mapping()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _build_mapping_queue(self) -> None:
        data = self._entry.data
        self._mapping_queue = []
        for ft in data.get(CONF_FISH_TANKS, []):
            self._mapping_queue.append({
                "type": COMPONENT_FISH_TANK,
                "id": ft[CONF_FT_ID],
                "name": ft[CONF_FT_NAME],
                "sensor_type": "Aquaponic Sensor",
                "roles": AQUAPONIC_SENSOR_ROLES,
            })
        for pb in data.get(CONF_PLANT_BEDS, []):
            medium = pb[CONF_PB_MEDIUM]
            self._mapping_queue.append({
                "type": COMPONENT_PLANT_BED,
                "id": pb[CONF_PB_ID],
                "name": pb[CONF_PB_NAME],
                "sensor_type": SENSOR_TYPE_NAME[medium],
                "roles": PLANT_BED_ROLES_BY_MEDIUM[medium],
            })
        for gh in data.get(CONF_GREENHOUSES, []):
            self._mapping_queue.append({
                "type": COMPONENT_GREENHOUSE,
                "id": gh[CONF_GH_ID],
                "name": gh[CONF_GH_NAME],
                "sensor_type": "Environment Sensor",
                "roles": ENVIRONMENT_SENSOR_ROLES,
            })
        self._mapping_idx = 0

    # ------------------------------------------------------------------
    # Step 1 – Sensor-Mapping (für jede Komponente)
    # ------------------------------------------------------------------

    async def async_step_sensor_mapping(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if not self._mapping_queue:
            return await self.async_step_outbound()
        component = self._mapping_queue[self._mapping_idx]
        roles: list[str] = component["roles"]
        if user_input is not None:
            self._sensor_mapping[component["id"]] = {
                role: user_input.get(role) or None for role in roles
            }
            self._mapping_idx += 1
            if self._mapping_idx < len(self._mapping_queue):
                return await self.async_step_sensor_mapping()
            return await self.async_step_outbound()
        current = self._sensor_mapping.get(component["id"], {})
        schema: dict = {}
        for role in roles:
            existing = current.get(role)
            key = vol.Optional(role, default=existing) if existing else vol.Optional(role)
            schema[key] = EntitySelector(EntitySelectorConfig(domain="sensor"))
        return self.async_show_form(
            step_id="sensor_mapping",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "component_name": component["name"],
                "sensor_type": component["sensor_type"],
                "current": str(self._mapping_idx + 1),
                "total": str(len(self._mapping_queue)),
            },
        )

    # ------------------------------------------------------------------
    # Step 2 – Outbound-Einstellungen
    # ------------------------------------------------------------------

    async def async_step_outbound(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data={
                CONF_SENSOR_MAPPING: self._sensor_mapping,
                CONF_ENDPOINT_URL: user_input[CONF_ENDPOINT_URL],
                CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                CONF_INTERVAL_SECONDS: int(user_input[CONF_INTERVAL_SECONDS]),
                CONF_LOOKBACK_SECONDS: int(user_input[CONF_LOOKBACK_SECONDS]),
            })
        effective: dict = {**self._entry.data, **self._entry.options}
        return self.async_show_form(
            step_id="outbound",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_ENDPOINT_URL,
                    default=effective.get(CONF_ENDPOINT_URL, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
                vol.Optional(
                    CONF_API_KEY,
                    default=effective.get(CONF_API_KEY, ""),
                ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Required(
                    CONF_INTERVAL_SECONDS,
                    default=effective.get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS),
                ): NumberSelector(
                    NumberSelectorConfig(min=30, max=86400, step=30, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
                vol.Required(
                    CONF_LOOKBACK_SECONDS,
                    default=effective.get(CONF_LOOKBACK_SECONDS, DEFAULT_LOOKBACK_SECONDS),
                ): NumberSelector(
                    NumberSelectorConfig(min=60, max=604800, step=60, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
            }),
        )
