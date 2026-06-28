# LoopingPilot Adapter for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/github/v/release/EnkiPonics/plc_light_system)
![HA min version](https://img.shields.io/badge/HA-%3E%3D2024.1-blue)

A Home Assistant custom integration that maps sensor entities to **Loops** (named physical circuits) and feeds time-series data to **LoopingPilot** — the aquaponics analysis engine by [EnkiPonics](https://github.com/EnkiPonics).

---

## Zielarchitektur

```
[Mini-Computer]
├── Proxmox VE (Hypervisor, kostenlos)
│   ├── VM 110 – Home Assistant OS
│   │   └── HACS → LoopingPilot Adapter  (dieses Repository)
│   └── LXC 200 – Debian 12 (512 MB RAM)
│       └── LoopingPilot  (github.com/EnkiPonics/loopingpilot)
│           └── :8765/api/v1/feed/loop  ←── HA sendet hierhin
```

---

## System-Installation (Schritt-für-Schritt)

> **Für den Techniker:** Alle vier Schritte der Reihe nach ausführen.  
> Voraussetzungen: Mini-Computer mit 4+ GB RAM, 64 GB SSD, LAN-Anschluss, Internetzugang.

---

### Schritt 1 – Proxmox VE installieren

#### 1.1 ISO herunterladen und USB erstellen
1. **Proxmox VE ISO** herunterladen: [proxmox.com/en/downloads](https://www.proxmox.com/en/downloads) → Proxmox VE → aktuellste Version
2. ISO auf USB flashen: [Rufus](https://rufus.ie) (Windows) oder [balenaEtcher](https://etcher.balena.io)

#### 1.2 Installation
1. Mini-Computer vom USB booten (BIOS: USB-Boot aktivieren, Secure Boot deaktivieren)
2. **Install Proxmox VE (Graphical)** wählen
3. Festplatte wählen → **gesamte SSD** für Proxmox
4. Netzwerk konfigurieren:
   - **Feste IP** vergeben, z.B. `192.168.1.10/24` (LAN des Kunden anpassen)
   - Gateway = Router-IP des Kunden
   - DNS = `8.8.8.8`
   - Hostname z.B. `enkiponics.local`
5. Root-Passwort und E-Mail setzen → Installation starten (~5 Min)
6. Nach Neustart: Proxmox Web-UI erreichbar unter `https://<IP>:8006`

#### 1.3 No-Subscription-Repository einrichten (kein Lizenz-Nag)
Im Proxmox Web-UI → **Shell** (oder SSH als root):

```bash
# Enterprise-Repo deaktivieren
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/ceph.list 2>/dev/null || true

# No-Subscription-Repo hinzufügen
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  > /etc/apt/sources.list.d/pve-no-subscription.list

apt-get update && apt-get dist-upgrade -y
```

---

### Schritt 2 – Home Assistant OS VM einrichten

#### 2.1 Schnell-Installation via Community-Script (empfohlen)
Im Proxmox Web-UI → **Shell**:

```bash
bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/vm/haos-vm.sh)"
```

Das Script lädt HA OS herunter, erstellt die VM automatisch und startet sie.  
Standard-Einstellungen bestätigen. VM-ID notieren (Standard: nächste freie ID).

> **Alternativ manuell:** HA OS `.qcow2` von [github.com/home-assistant/operating-system/releases](https://github.com/home-assistant/operating-system/releases) herunterladen, VM anlegen, Disk importieren — Details: [HA Docs](https://www.home-assistant.io/installation/generic-x86-64).

#### 2.2 Home Assistant einrichten
1. HA Web-UI aufrufen: `http://<HA-IP>:8123` (IP im Proxmox unter der VM sichtbar)
2. **Onboarding** abschließen: Admin-Benutzer anlegen, Zeitzone setzen
3. **Einstellungen → System → Netzwerk**: Feste IP vergeben (z.B. `192.168.1.11`)

#### 2.3 HACS installieren
Im Proxmox Web-UI → Shell (oder SSH auf Proxmox):

```bash
# HACS-Installer direkt im HA-Container ausführen
bash -c "$(wget -qO- https://get.hacs.xyz)"
```

Falls das nicht klappt — über Proxmox qm guest exec:

```bash
qm guest exec <VM-ID> -- bash -c \
  "wget -qO- https://get.hacs.xyz | bash -"
```

Nach der Installation: HA neu starten → HACS erscheint unter **Einstellungen → Integrationen**.  
HACS öffnen → GitHub-OAuth abschließen.

#### 2.4 Mosquitto MQTT Broker (optional, für spätere Phasen)
**Einstellungen → Add-ons → Add-on Store → Mosquitto broker** → Installieren → Starten → Autostart aktivieren.

---

### Schritt 3 – LoopingPilot einrichten (Debian LXC)

#### Option A: Automatisch via PowerShell-Script (von Windows-PC)
Voraussetzung: [PuTTY/plink](https://www.putty.org) installiert.

```powershell
# Script aus dem SmartHome-Repo ausführen
.\setup_loopingpilot_lxc.ps1
```

Das Script erstellt den LXC-Container, installiert LoopingPilot und richtet den systemd-Service ein.  
Am Ende gibt es die IP des LXC aus — diese für Schritt 4 notieren.

#### Option B: Manuell im Proxmox Web-UI

**3.1 LXC-Container erstellen**

Proxmox Web-UI → **Datacenter → Create CT**:

| Feld | Wert |
|------|------|
| CT ID | `200` |
| Hostname | `loopingpilot` |
| Password | frei wählbar |
| Template | `debian-12-standard_*.tar.zst` (ggf. zuerst unter *CT Templates* herunterladen) |
| Disk | 4 GB, Storage: `local-lvm` |
| CPU | 2 Cores |
| Memory | 512 MB, Swap 256 MB |
| Network | Bridge `vmbr0`, DHCP (oder feste IP) |
| Unprivileged | ✅ |

Container starten.

**3.2 LoopingPilot installieren**

Proxmox Web-UI → Container 200 → **Console**:

```bash
apt-get update && apt-get install -y python3-venv git

cd /opt
git clone https://github.com/EnkiPonics/loopingpilot.git
cd loopingpilot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

**3.3 systemd-Service anlegen**

```bash
cat > /etc/systemd/system/loopingpilot.service << 'EOF'
[Unit]
Description=LoopingPilot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/loopingpilot/src
ExecStart=/opt/loopingpilot/.venv/bin/python -m loopingpilot
Restart=always
RestartSec=5
EnvironmentFile=/opt/loopingpilot/.env

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable loopingpilot
systemctl start loopingpilot
```

**3.4 Verifizieren**

```bash
systemctl status loopingpilot
curl http://localhost:8765/health
# Erwartete Antwort: {"status":"ok"}
```

IP des LXC notieren:
```bash
hostname -I
```

---

### Schritt 4 – LoopingPilot Adapter in Home Assistant einrichten

#### 4.1 Adapter via HACS installieren
1. HA Web-UI → **HACS → Integrationen → ⋮ → Custom repositories**
2. URL: `https://github.com/EnkiPonics/plc_light_system` — Kategorie: **Integration**
3. **LoopingPilot Adapter** → **Herunterladen**
4. HA neu starten

#### 4.2 Integration konfigurieren
**Einstellungen → Integrationen → Integration hinzufügen → LoopingPilot Adapter**

Der Konfigurations-Wizard führt durch folgende Schritte:

| Schritt | Was eintragen |
|---------|---------------|
| Loop-Name | Name des Kreislaufs, z.B. `Fischtank 1` |
| Greenhouses | Anzahl Gewächshäuser (0 wenn keins vorhanden) |
| Fish Tanks | Anzahl Fischtanks (mind. 1) |
| Plant Beds | Anzahl Pflanzbeete (mind. 1) |
| Sensor-Mapping | HA-Sensor-Entities den Messrollen zuordnen (alle optional) |
| Endpoint URL | `http://<LXC-IP>:8765/api/v1/feed/loop` ← IP aus Schritt 3 |
| API Key | leer lassen |
| Sendeintervall | 300 Sekunden (Standard) |

#### 4.3 Funktionstest
Nach dem ersten Intervall (max. 5 Minuten):

**HA-Logs** (Einstellungen → System → Logs):
```
INFO (loopingpilot): Feed gesendet: loop=Fischtank 1 receipt_id=...
```

**LoopingPilot-Logs** (Proxmox → LXC 200 → Console):
```bash
journalctl -u loopingpilot -f
```
```json
{"level": "INFO", "msg": "Loop processed", "loop_name": "Fischtank 1", "module": "DummyLSTM", "status": "ok"}
```

**Wenn beide Meldungen erscheinen: Installation erfolgreich ✅**

---

## Updates

### LoopingPilot Adapter aktualisieren
HA → HACS → Integrationen → LoopingPilot Adapter → **Update** (erscheint automatisch bei neuer Version)

### LoopingPilot aktualisieren
LXC-Console (Proxmox → Container 200 → Console):

```bash
cd /opt/loopingpilot
git pull
.venv/bin/pip install -r requirements.txt
systemctl restart loopingpilot
```

---

## Was ist ein Loop?

A Loop is a named physical circuit, for example: fish tank + biofilter + plant bed. Any HA sensor entity can be assigned to a Loop role (water temperature, pH, EC, dissolved oxygen, …). Unmapped entities are invisible to LoopingPilot.

---

## Lizenz

Copyright (c) 2026 Anett Waßmann. All rights reserved.  
Unauthorised use, reproduction or distribution is prohibited.

