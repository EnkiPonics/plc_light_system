# LoopingPilot Adapter for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/EnkiPonics/plc_light_system)
![HA min version](https://img.shields.io/badge/HA-%3E%3D2024.1-blue)

A Home Assistant custom integration that maps sensor entities to **Loops** (named physical circuits) and feeds time-series data to **LoopingPilot** — the aquaponics analysis engine by [EnkiPonics](https://github.com/EnkiPonics).

---

## What is a Loop?

A Loop is a named physical circuit, for example: fish tank + biofilter + plant bed. Any HA sensor entity can be assigned to a Loop role (water temperature, pH, EC, dissolved oxygen, …). Unmapped entities are invisible to LoopingPilot.

---

## Installation via HACS

1. Open HACS in Home Assistant
2. Click **⋮ → Custom repositories**
3. Add `https://github.com/EnkiPonics/plc_light_system` — Category: **Integration**
4. Find **LoopingPilot Adapter** → **Download**
5. Restart Home Assistant
6. Go to **Settings → Integrations → Add Integration → LoopingPilot Adapter**

---

## Requirements

- Home Assistant ≥ 2024.1
- LoopingPilot endpoint (stub provided in `/stub/stub_server.py` for development)
- Optional: Mosquitto MQTT broker (for MQTT outbound channel, Phase 5)

---

## Status

| Version | Phase | Status |
|---|---|---|
| `0.1.0` | Integration skeleton loads | ✅ Released |
| `0.2.0` | Config Flow / GUI mapping | ✅ Released |
| `0.3.0` | Recorder history feed | 🔧 In progress |
| `0.4.0` | Outbound feed to LoopingPilot | 📋 Planned |
| `1.0.0` | First stable release | 📋 Planned |


