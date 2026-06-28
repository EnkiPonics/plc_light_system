# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Options flow for LoopingPilot. (Phase 2 – Stub)"""
from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class LoopingPilotOptionsFlow(config_entries.OptionsFlow):
    """Handle LoopingPilot options (nachträgliche Konfigurationsänderung)."""

    # Phase 2: Mapping und Intervall nachträglich änderbar machen
