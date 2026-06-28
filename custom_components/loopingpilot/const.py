# Copyright (c) 2026 Anett Waßmann. All rights reserved.
# Unauthorised use, reproduction or distribution is prohibited.
"""Constants for the LoopingPilot integration."""

DOMAIN = "loopingpilot"

# ---------------------------------------------------------------------------
# Physical component types
# ---------------------------------------------------------------------------
COMPONENT_FISH_TANK = "fish_tank"
COMPONENT_PLANT_BED = "plant_bed"
COMPONENT_GREENHOUSE = "greenhouse"

# Plant bed medium types
MEDIUM_HYDROPONIC = "hydroponic"   # Wurzeln hängen direkt im Wasser
MEDIUM_SOIL = "soil"               # Substrat / Erde / Wasser läuft durch

# Sentinel für "kein Greenhouse zugeordnet"
NO_GREENHOUSE = "__none__"

# ---------------------------------------------------------------------------
# Sensor-Produkte und ihre Messrollen
# ---------------------------------------------------------------------------

# Aquaponic Sensor – Wasserqualität (Fish Tanks + hydroponic Plant Beds)
AQUAPONIC_SENSOR_ROLES: list[str] = [
    "water_temp",    # °C       – Wassertemperatur
    "ph",            # pH       – pH-Wert
    "do",            # mg/L     – gelöster Sauerstoff (Dissolved Oxygen)
    "ec",            # µS/cm    – elektrische Leitfähigkeit (Nährstoffe)
    "water_level",   # cm / %   – Wasserstand
]

# Hydroponic Sensor – Substrat/Boden (soil Plant Beds)
# Hinweis: Bezeichnung aus Produktspezifikation; ggf. umbenennen (offene Entscheidung)
HYDROPONIC_SENSOR_ROLES: list[str] = [
    "soil_temp",           # °C    – Substrat-/Bodentemperatur
    "substrate_moisture",  # %     – Substratfeuchte
    "ph",                  # pH    – pH-Wert
    "ec",                  # µS/cm – elektrische Leitfähigkeit (Nährstoffe)
]

# Environment Sensor – Klima (Greenhouses)
ENVIRONMENT_SENSOR_ROLES: list[str] = [
    "air_temp",   # °C         – Lufttemperatur
    "humidity",   # %          – relative Luftfeuchtigkeit
    "co2",        # ppm        – CO₂-Konzentration
    "par_ppfd",   # µmol/m²/s – Photosynthetisch aktive Strahlung (PAR/PPFD)
    "vpd",        # kPa        – Sättigungsdefizit (Vapor Pressure Deficit)
    "leaf_temp",  # °C         – Blatttemperatur (IR, Kondensationsrisiko)
]

# Aliases für Rückwärtskompatibilität
FISH_TANK_ROLES = AQUAPONIC_SENSOR_ROLES
GREENHOUSE_ROLES = ENVIRONMENT_SENSOR_ROLES

# Plant Bed: Rollen abhängig vom Substrattyp
PLANT_BED_ROLES_BY_MEDIUM: dict[str, list[str]] = {
    MEDIUM_HYDROPONIC: AQUAPONIC_SENSOR_ROLES,  # Wurzeln im Wasser → Aquaponic Sensor
    MEDIUM_SOIL:       HYDROPONIC_SENSOR_ROLES,  # Substrat/Erde     → Hydroponic Sensor
}

# Sensor-Typname zur Anzeige im Config Flow
SENSOR_TYPE_NAME: dict[str, str] = {
    MEDIUM_HYDROPONIC: "Aquaponic Sensor",
    MEDIUM_SOIL:       "Hydroponic Sensor",
}

ROLES_BY_COMPONENT: dict[str, list[str]] = {
    COMPONENT_FISH_TANK:  AQUAPONIC_SENSOR_ROLES,
    COMPONENT_GREENHOUSE: ENVIRONMENT_SENSOR_ROLES,
    # Plant Bed: medium-abhängig, wird im Config Flow per PLANT_BED_ROLES_BY_MEDIUM aufgelöst
}

# ---------------------------------------------------------------------------
# Configuration keys
# ---------------------------------------------------------------------------
CONF_LOOP_NAME = "loop_name"

# Greenhouses
CONF_GREENHOUSES = "greenhouses"
CONF_GH_ID = "gh_id"
CONF_GH_NAME = "gh_name"
CONF_GH_VOLUME_M3 = "gh_volume_m3"

# Fish Tanks
CONF_FISH_TANKS = "fish_tanks"
CONF_FT_ID = "ft_id"
CONF_FT_NAME = "ft_name"
CONF_FT_VOLUME_L = "ft_volume_l"
CONF_FT_GREENHOUSE = "ft_greenhouse"

# Plant Beds
CONF_PLANT_BEDS = "plant_beds"
CONF_PB_ID = "pb_id"
CONF_PB_NAME = "pb_name"
CONF_PB_VOLUME_L = "pb_volume_l"
CONF_PB_MEDIUM = "pb_medium"
CONF_PB_GREENHOUSE = "pb_greenhouse"

# Sensor mapping
CONF_SENSOR_MAPPING = "sensor_mapping"

# Outbound
CONF_ENDPOINT_URL = "endpoint_url"
CONF_API_KEY = "api_key"
CONF_INTERVAL_SECONDS = "interval_seconds"
CONF_LOOKBACK_SECONDS = "lookback_seconds"

# Defaults
DEFAULT_INTERVAL_SECONDS: int = 300    # 5 Minuten
DEFAULT_LOOKBACK_SECONDS: int = 3600   # 60 Minuten
