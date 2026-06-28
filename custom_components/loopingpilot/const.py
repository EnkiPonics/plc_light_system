# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Constants for the LoopingPilot integration."""

DOMAIN = "loopingpilot"

# ---------------------------------------------------------------------------
# Konfigurations-Keys (Config Entry / Config Flow)
# ---------------------------------------------------------------------------
CONF_LOOPS = "loops"
CONF_LOOP_ID = "loop_id"
CONF_LOOP_NAME = "loop_name"
CONF_ROLES = "roles"
CONF_ROLE = "role"
CONF_ENTITY_ID = "entity_id"
CONF_ENDPOINT_URL = "endpoint_url"
CONF_API_KEY = "api_key"
CONF_INTERVAL_SECONDS = "interval_seconds"
CONF_LOOKBACK_SECONDS = "lookback_seconds"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_INTERVAL_SECONDS: int = 300    # 5 Minuten
DEFAULT_LOOKBACK_SECONDS: int = 3600   # 60 Minuten

# ---------------------------------------------------------------------------
# Loop-Rollen
# Jede Rolle repräsentiert einen Messparameter innerhalb eines Loops.
# ---------------------------------------------------------------------------
LOOP_ROLES: list[str] = [
    "water_temp",       # °C   – Wassertemperatur
    "ph",               # pH   – pH-Wert
    "ec",               # µS/cm – elektrische Leitfähigkeit
    "do",               # mg/L  – gelöster Sauerstoff
    "flow_rate",        # L/h   – Durchflussrate
    "ammonia",          # mg/L  – Ammoniak / Ammonium (NH3/NH4)
    "nitrite",          # mg/L  – Nitrit (NO2)
    "nitrate",          # mg/L  – Nitrat (NO3)
    "water_level",      # cm / % – Wasserstand
    "ambient_temp",     # °C   – Umgebungstemperatur
    "light_intensity",  # lux  – Lichtintensität
    "co2",              # ppm  – CO₂-Konzentration
    "custom",           # frei definierbar
]
