# setup_loopingpilot_lxc.ps1
# Richtet den LoopingPilot LXC auf dem Proxmox-Host komplett ein.
#
# Da das LoopingPilot-Repo privat ist, wird der Quellcode vom lokalen Rechner
# per pscp auf den Proxmox-Host übertragen. Die venv wird dort gebaut
# (gleiche Arch + Python-Version wie LXC) und als Bundle in den LXC geschoben.
#
# Voraussetzungen:
#   - plink.exe / pscp.exe im PATH (PuTTY)
#   - Proxmox läuft, Host hat Internetzugang
#   - loopingpilot-Repo lokal vorhanden
#
# Verwendung:
#   .\setup_loopingpilot_lxc.ps1
#   .\setup_loopingpilot_lxc.ps1 -LxcId 201 -LxcIp "192.168.178.175/24"

param(
    [string]$LxcId     = "200",
    [string]$LxcIp     = "dhcp",
    [string]$LxcGw     = "192.168.178.1",
    [string]$LxcPass   = "loopingpilot",
    [string]$LpRepo    = "C:\PROJECTS\CoFounding\Enkiponics\repository\loopingpilot",
    [switch]$SkipCreate         # LXC existiert bereits, nur Software einrichten
)

# Zugangsdaten aus .env laden (nicht im Repo)
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "FEHLER: $envFile nicht gefunden." -ForegroundColor Red
    Write-Host "Bitte scripts\.env.example kopieren, zu scripts\.env umbenennen und anpassen." -ForegroundColor Yellow
    exit 1
}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)=(.+)$') {
        Set-Variable -Name $Matches[1] -Value $Matches[2].Trim()
    }
}
$PROXMOX_IP = $PROXMOX_IP
$PROXMOX_PW = $PROXMOX_PW
$HOST_KEY   = $PROXMOX_HOST_KEY

$TEMP_DIR = "$env:TEMP\lp_deploy"

# ---------------------------------------------------------------------------
function Invoke-Prox([string]$Cmd) {
    $out = & plink -batch -pw $PROXMOX_PW -hostkey $HOST_KEY `
           "root@$PROXMOX_IP" $Cmd 2>&1
    Write-Host $out
    return $out
}
function Upload([string]$Local, [string]$Remote) {
    & pscp -batch -pw $PROXMOX_PW -hostkey $HOST_KEY $Local "root@${PROXMOX_IP}:$Remote" | Out-Null
}
function Step([string]$Msg) { Write-Host "`n=== $Msg ===" -ForegroundColor Cyan }
function Ok([string]$Msg)   { Write-Host $Msg -ForegroundColor Green }
function Warn([string]$Msg) { Write-Host $Msg -ForegroundColor Yellow }
function Fail([string]$Msg) { Write-Host "FEHLER: $Msg" -ForegroundColor Red; exit 1 }
# ---------------------------------------------------------------------------

New-Item -ItemType Directory -Force $TEMP_DIR | Out-Null

# --- LXC anlegen -----------------------------------------------------------
if (-not $SkipCreate) {
    Step "Schritt 1: Debian-12-Template suchen / herunterladen"
    $tmpl = (Invoke-Prox "pveam list local 2>/dev/null | grep debian-12 | tail -1 | awk '{print `$1}'").Trim()
    if (-not $tmpl) {
        Warn "Template nicht lokal – lade herunter..."
        Invoke-Prox "pveam update" | Out-Null
        $avail = (Invoke-Prox "pveam available --section system | grep debian-12-standard | tail -1 | awk '{print `$2}'").Trim()
        Invoke-Prox "pveam download local $avail" | Out-Null
        $tmpl = (Invoke-Prox "pveam list local 2>/dev/null | grep debian-12 | tail -1 | awk '{print `$1}'").Trim()
    }
    Ok "Template: $tmpl"

    Step "Schritt 2: LXC $LxcId erstellen"
    $netCfg = if ($LxcIp -eq "dhcp") { "name=eth0,bridge=vmbr0,ip=dhcp" } `
              else { "name=eth0,bridge=vmbr0,ip=$LxcIp,gw=$LxcGw" }
    Invoke-Prox @"
pct create $LxcId $tmpl \
  --hostname loopingpilot \
  --password $LxcPass \
  --memory 512 --swap 256 --cores 2 \
  --rootfs local-lvm:4 \
  --net0 $netCfg \
  --unprivileged 1 --features nesting=1 \
  --start 1
"@
    Warn "Warte 8 Sekunden..."
    Start-Sleep -Seconds 8

    Step "Schritt 3: python3-venv im LXC installieren"
    Invoke-Prox "pct exec $LxcId -- bash -c 'apt-get update -qq && apt-get install -y python3-venv -qq'"
} else {
    Warn "-SkipCreate gesetzt: LXC-Erstellung übersprungen."
}

# --- Quellcode verpacken ----------------------------------------------------
Step "Schritt 4: Quellcode verpacken"
if (-not (Test-Path $LpRepo)) { Fail "Repo nicht gefunden: $LpRepo" }

$zipPath = "$TEMP_DIR\lp_src.zip"
Compress-Archive -Path "$LpRepo\src","$LpRepo\requirements.txt","$LpRepo\.env.example" `
    -DestinationPath $zipPath -Force
Ok "ZIP: $([math]::Round((Get-Item $zipPath).Length/1KB,1)) KB"

# --- Setup-Skript erstellen -------------------------------------------------
$setupSh = "$TEMP_DIR\lp_setup.sh"
@'
#!/bin/bash
set -e

# ZIP entpacken (Windows-Backslash-kompatibel via Python)
rm -rf /opt/loopingpilot
python3 -c "
import zipfile, os
z = zipfile.ZipFile('/tmp/lp_src.zip')
for m in z.namelist():
    name = m.replace('\\\\', '/')
    dest = os.path.join('/opt/loopingpilot', name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not name.endswith('/'):
        with open(dest, 'wb') as f:
            f.write(z.read(m))
print('Entpackt.')
"

# .env anlegen
cp /opt/loopingpilot/.env.example /opt/loopingpilot/.env

# Venv auf Proxmox-Host anlegen (gleiche Python/Arch wie LXC)
python3 -m venv /opt/loopingpilot/.venv
/opt/loopingpilot/.venv/bin/pip install --quiet -r /opt/loopingpilot/requirements.txt
echo "Venv: $(/opt/loopingpilot/.venv/bin/python -V)"

# Bundle erstellen und in LXC pushen
tar czf /tmp/lp_bundle.tar.gz -C /opt loopingpilot
echo "Bundle: $(du -sh /tmp/lp_bundle.tar.gz | cut -f1)"
pct push LXC_ID /tmp/lp_bundle.tar.gz /tmp/lp_bundle.tar.gz
pct exec LXC_ID -- bash -c "rm -rf /opt/loopingpilot && tar xzf /tmp/lp_bundle.tar.gz -C /opt"
echo "LXC-Inhalt: $(pct exec LXC_ID -- ls /opt/loopingpilot/)"

# systemd-Service schreiben
pct exec LXC_ID -- bash -c 'cat > /etc/systemd/system/loopingpilot.service << EOF
[Unit]
Description=LoopingPilot AI Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/loopingpilot
EnvironmentFile=/opt/loopingpilot/.env
Environment=PYTHONPATH=/opt/loopingpilot/src
ExecStart=/opt/loopingpilot/.venv/bin/python -m uvicorn loopingpilot.main:app --host 0.0.0.0 --port 8765
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable loopingpilot
systemctl start loopingpilot'

sleep 4
pct exec LXC_ID -- systemctl status loopingpilot --no-pager | head -10
IP=$(pct exec LXC_ID -- hostname -I | awk '{print $1}')
echo "Service-IP: $IP"
python3 -c "
import urllib.request
try:
    r = urllib.request.urlopen('http://$IP:8765/health', timeout=5)
    print('Health-Check:', r.read().decode())
except Exception as e:
    print('Health-Check fehlgeschlagen:', e)
"
echo "FERTIG"
'@ -replace 'LXC_ID', $LxcId | Set-Content -Encoding UTF8 -Path $setupSh
# BOM entfernen (Set-Content UTF8 fügt BOM ein)
$bytes = [System.IO.File]::ReadAllBytes($setupSh)
if ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    [System.IO.File]::WriteAllBytes($setupSh, $bytes[3..($bytes.Length-1)])
}

# --- Dateien hochladen und ausführen ----------------------------------------
Step "Schritt 5: Upload + Ausführung auf Proxmox-Host"
Upload $zipPath "/tmp/lp_src.zip"
Upload $setupSh "/tmp/lp_setup.sh"
Invoke-Prox "bash /tmp/lp_setup.sh 2>&1"

Ok "`nSetup abgeschlossen."
Write-Host "Naechster Schritt: HA-Adapter konfigurieren mit Endpoint http://<LXC-IP>:8765/api/v1/feed/loop"
