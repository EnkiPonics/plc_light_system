# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Config flow for LoopingPilot."""
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
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    AQUAPONIC_SENSOR_ROLES,
    COMPONENT_FISH_TANK,
    COMPONENT_GREENHOUSE,
    COMPONENT_PLANT_BED,
    ENVIRONMENT_SENSOR_ROLES,
    CONF_API_KEY,
    CONF_ENDPOINT_URL,
    CONF_FISH_TANKS,
    CONF_FT_GREENHOUSE,
    CONF_FT_ID,
    CONF_FT_NAME,
    CONF_FT_VOLUME_L,
    CONF_GH_ID,
    CONF_GH_NAME,
    CONF_GH_VOLUME_M3,
    CONF_GREENHOUSES,
    CONF_INTERVAL_SECONDS,
    CONF_LOOKBACK_SECONDS,
    CONF_LOOP_NAME,
    CONF_PB_GREENHOUSE,
    CONF_PB_ID,
    CONF_PB_MEDIUM,
    CONF_PB_NAME,
    CONF_PB_VOLUME_L,
    CONF_PLANT_BEDS,
    CONF_SENSOR_MAPPING,
    DEFAULT_INTERVAL_SECONDS,
    DEFAULT_LOOKBACK_SECONDS,
    DOMAIN,
    HYDROPONIC_SENSOR_ROLES,
    MEDIUM_HYDROPONIC,
    MEDIUM_SOIL,
    NO_GREENHOUSE,
    PLANT_BED_ROLES_BY_MEDIUM,
    ROLES_BY_COMPONENT,
    SENSOR_TYPE_NAME,
)


class LoopingPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Wizard: Loop-Struktur und Sensor-Mapping konfigurieren."""

    VERSION = 1

    def __init__(self) -> None:
        self._loop_name: str = ""
        self._greenhouses: list[dict] = []
        self._gh_count: int = 0
        self._gh_idx: int = 0
        self._fish_tanks: list[dict] = []
        self._ft_count: int = 0
        self._ft_idx: int = 0
        self._plant_beds: list[dict] = []
        self._pb_count: int = 0
        self._pb_idx: int = 0
        self._mapping_queue: list[dict] = []
        self._mapping_idx: int = 0
        self._sensor_mapping: dict[str, dict[str, str | None]] = {}

    # ------------------------------------------------------------------
    # Step 1 – Loop-Name
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            self._loop_name = user_input[CONF_LOOP_NAME]
            return await self.async_step_greenhouses_count()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_LOOP_NAME): TextSelector()}),
        )

    # ------------------------------------------------------------------
    # Step 2 – Anzahl Greenhouses
    # ------------------------------------------------------------------

    async def async_step_greenhouses_count(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._gh_count = int(user_input["gh_count"])
            self._gh_idx = 0
            self._greenhouses = []
            if self._gh_count > 0:
                return await self.async_step_greenhouse()
            return await self.async_step_fish_tanks_count()
        return self.async_show_form(
            step_id="greenhouses_count",
            data_schema=vol.Schema({
                vol.Required("gh_count", default=0): NumberSelector(
                    NumberSelectorConfig(min=0, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
            }),
        )

    # ------------------------------------------------------------------
    # Step 3 – Greenhouse-Details (wiederholt für jeden)
    # ------------------------------------------------------------------

    async def async_step_greenhouse(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._greenhouses.append({
                CONF_GH_ID: f"gh{self._gh_idx + 1}",
                CONF_GH_NAME: user_input[CONF_GH_NAME],
                CONF_GH_VOLUME_M3: user_input.get(CONF_GH_VOLUME_M3),
            })
            self._gh_idx += 1
            if self._gh_idx < self._gh_count:
                return await self.async_step_greenhouse()
            return await self.async_step_fish_tanks_count()
        idx = self._gh_idx + 1
        return self.async_show_form(
            step_id="greenhouse",
            data_schema=vol.Schema({
                vol.Required(CONF_GH_NAME, default=f"Greenhouse {idx}"): TextSelector(),
                vol.Optional(CONF_GH_VOLUME_M3): NumberSelector(
                    NumberSelectorConfig(min=0.1, max=999999, step=0.1, mode=NumberSelectorMode.BOX, unit_of_measurement="m³")
                ),
            }),
            description_placeholders={"current": str(idx), "total": str(self._gh_count)},
        )

    # ------------------------------------------------------------------
    # Step 4 – Anzahl Fish Tanks
    # ------------------------------------------------------------------

    async def async_step_fish_tanks_count(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._ft_count = int(user_input["ft_count"])
            self._ft_idx = 0
            self._fish_tanks = []
            return await self.async_step_fish_tank()
        return self.async_show_form(
            step_id="fish_tanks_count",
            data_schema=vol.Schema({
                vol.Required("ft_count", default=1): NumberSelector(
                    NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
            }),
        )

    # ------------------------------------------------------------------
    # Step 5 – Fish-Tank-Details (wiederholt für jeden)
    # ------------------------------------------------------------------

    async def async_step_fish_tank(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            gh_val = user_input.get(CONF_FT_GREENHOUSE)
            self._fish_tanks.append({
                CONF_FT_ID: f"ft{self._ft_idx + 1}",
                CONF_FT_NAME: user_input[CONF_FT_NAME],
                CONF_FT_VOLUME_L: user_input.get(CONF_FT_VOLUME_L),
                CONF_FT_GREENHOUSE: None if gh_val == NO_GREENHOUSE else gh_val,
            })
            self._ft_idx += 1
            if self._ft_idx < self._ft_count:
                return await self.async_step_fish_tank()
            return await self.async_step_plant_beds_count()
        idx = self._ft_idx + 1
        schema: dict = {
            vol.Required(CONF_FT_NAME, default=f"Fish Tank {idx}"): TextSelector(),
            vol.Optional(CONF_FT_VOLUME_L): NumberSelector(
                NumberSelectorConfig(min=1, max=1000000, step=1, mode=NumberSelectorMode.BOX, unit_of_measurement="L")
            ),
        }
        if self._greenhouses:
            gh_options = [{"label": "– kein Greenhouse –", "value": NO_GREENHOUSE}] + [
                {"label": gh[CONF_GH_NAME], "value": gh[CONF_GH_ID]} for gh in self._greenhouses
            ]
            schema[vol.Optional(CONF_FT_GREENHOUSE, default=NO_GREENHOUSE)] = SelectSelector(
                SelectSelectorConfig(options=gh_options, mode=SelectSelectorMode.DROPDOWN)
            )
        return self.async_show_form(
            step_id="fish_tank",
            data_schema=vol.Schema(schema),
            description_placeholders={"current": str(idx), "total": str(self._ft_count)},
        )

    # ------------------------------------------------------------------
    # Step 6 – Anzahl Plant Beds
    # ------------------------------------------------------------------

    async def async_step_plant_beds_count(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._pb_count = int(user_input["pb_count"])
            self._pb_idx = 0
            self._plant_beds = []
            return await self.async_step_plant_bed()
        return self.async_show_form(
            step_id="plant_beds_count",
            data_schema=vol.Schema({
                vol.Required("pb_count", default=1): NumberSelector(
                    NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
            }),
        )

    # ------------------------------------------------------------------
    # Step 7 – Plant-Bed-Details (wiederholt für jedes)
    # ------------------------------------------------------------------

    async def async_step_plant_bed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            gh_val = user_input.get(CONF_PB_GREENHOUSE)
            self._plant_beds.append({
                CONF_PB_ID: f"pb{self._pb_idx + 1}",
                CONF_PB_NAME: user_input[CONF_PB_NAME],
                CONF_PB_VOLUME_L: user_input.get(CONF_PB_VOLUME_L),
                CONF_PB_MEDIUM: user_input[CONF_PB_MEDIUM],
                CONF_PB_GREENHOUSE: None if gh_val == NO_GREENHOUSE else gh_val,
            })
            self._pb_idx += 1
            if self._pb_idx < self._pb_count:
                return await self.async_step_plant_bed()
            self._build_mapping_queue()
            return await self.async_step_sensor_mapping()
        idx = self._pb_idx + 1
        medium_options = [
            {"label": "Hydroponic (Wurzeln im Wasser)", "value": MEDIUM_HYDROPONIC},
            {"label": "Soil / Substrat (Wasser durchläuft Boden)", "value": MEDIUM_SOIL},
        ]
        schema: dict = {
            vol.Required(CONF_PB_NAME, default=f"Plant Bed {idx}"): TextSelector(),
            vol.Optional(CONF_PB_VOLUME_L): NumberSelector(
                NumberSelectorConfig(min=0.1, max=999999, step=0.1, mode=NumberSelectorMode.BOX, unit_of_measurement="L")
            ),
            vol.Required(CONF_PB_MEDIUM, default=MEDIUM_HYDROPONIC): SelectSelector(
                SelectSelectorConfig(options=medium_options, mode=SelectSelectorMode.DROPDOWN)
            ),
        }
        if self._greenhouses:
            gh_options = [{"label": "– kein Greenhouse –", "value": NO_GREENHOUSE}] + [
                {"label": gh[CONF_GH_NAME], "value": gh[CONF_GH_ID]} for gh in self._greenhouses
            ]
            schema[vol.Optional(CONF_PB_GREENHOUSE, default=NO_GREENHOUSE)] = SelectSelector(
                SelectSelectorConfig(options=gh_options, mode=SelectSelectorMode.DROPDOWN)
            )
        return self.async_show_form(
            step_id="plant_bed",
            data_schema=vol.Schema(schema),
            description_placeholders={"current": str(idx), "total": str(self._pb_count)},
        )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _build_mapping_queue(self) -> None:
        self._mapping_queue = []
        for ft in self._fish_tanks:
            self._mapping_queue.append({
                "type": COMPONENT_FISH_TANK,
                "id": ft[CONF_FT_ID],
                "name": ft[CONF_FT_NAME],
                "sensor_type": "Aquaponic Sensor",
                "roles": AQUAPONIC_SENSOR_ROLES,
            })
        for pb in self._plant_beds:
            medium = pb[CONF_PB_MEDIUM]
            self._mapping_queue.append({
                "type": COMPONENT_PLANT_BED,
                "id": pb[CONF_PB_ID],
                "name": pb[CONF_PB_NAME],
                "sensor_type": SENSOR_TYPE_NAME[medium],
                "roles": PLANT_BED_ROLES_BY_MEDIUM[medium],
            })
        for gh in self._greenhouses:
            self._mapping_queue.append({
                "type": COMPONENT_GREENHOUSE,
                "id": gh[CONF_GH_ID],
                "name": gh[CONF_GH_NAME],
                "sensor_type": "Environment Sensor",
                "roles": ENVIRONMENT_SENSOR_ROLES,
            })
        self._mapping_idx = 0

    # ------------------------------------------------------------------
    # Step 8 – Sensor-Mapping (eine Komponente nach der anderen)
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
        return self.async_show_form(
            step_id="sensor_mapping",
            data_schema=vol.Schema({
                vol.Optional(role): EntitySelector(EntitySelectorConfig(domain="sensor"))
                for role in roles
            }),
            description_placeholders={
                "component_name": component["name"],
                "sensor_type": component["sensor_type"],
                "current": str(self._mapping_idx + 1),
                "total": str(len(self._mapping_queue)),
            },
        )

    # ------------------------------------------------------------------
    # Step 9 – Outbound-Konfiguration
    # ------------------------------------------------------------------

    async def async_step_outbound(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=f"LoopingPilot – {self._loop_name}",
                data={
                    CONF_LOOP_NAME: self._loop_name,
                    CONF_GREENHOUSES: self._greenhouses,
                    CONF_FISH_TANKS: self._fish_tanks,
                    CONF_PLANT_BEDS: self._plant_beds,
                    CONF_SENSOR_MAPPING: self._sensor_mapping,
                    CONF_ENDPOINT_URL: user_input[CONF_ENDPOINT_URL],
                    CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                    CONF_INTERVAL_SECONDS: int(user_input[CONF_INTERVAL_SECONDS]),
                    CONF_LOOKBACK_SECONDS: int(user_input[CONF_LOOKBACK_SECONDS]),
                },
            )
        return self.async_show_form(
            step_id="outbound",
            data_schema=vol.Schema({
                vol.Required(CONF_ENDPOINT_URL): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Optional(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_INTERVAL_SECONDS, default=DEFAULT_INTERVAL_SECONDS): NumberSelector(
                    NumberSelectorConfig(min=30, max=86400, step=30, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
                vol.Required(CONF_LOOKBACK_SECONDS, default=DEFAULT_LOOKBACK_SECONDS): NumberSelector(
                    NumberSelectorConfig(min=60, max=604800, step=60, mode=NumberSelectorMode.BOX, unit_of_measurement="s")
                ),
            }),
        )

