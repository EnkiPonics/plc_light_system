# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Config flow for LoopingPilot. (Phase 2 – Stub)"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class LoopingPilotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LoopingPilot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Erster Schritt – Platzhalter bis Phase 2 implementiert ist."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title="LoopingPilot Adapter", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "info": "Konfiguration folgt in Phase 2. Klicke Senden um fortzufahren."
            },
        )

    # Phase 2: Vollständige Schritte implementieren
    # - Schritt 1: Loops definieren (Name + ID)
    # - Schritt 2: Entity-Mapping pro Loop
    # - Schritt 3: Outbound-Konfiguration (URL, API-Key, Intervall)
