# update_loopingpilot_lxc.ps1
# Schiebt aktualisierten LoopingPilot-Quellcode in den LXC.
#
# Wird nur src/ aktualisiert (kein Rebuild der venv).
# Pycache wird geleert, Service neu gestartet.
#
# Verwendung:
#   .\update_loopingpilot_lxc.ps1
#   .\update_loopingpilot_lxc.ps1 -LxcId 201

param(
    [string]$LxcId  = "200",
    [string]$LpRepo = "C:\PROJECTS\CoFounding\Enkiponics\repository\loopingpilot"
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
function Fail([string]$Msg) { Write-Host "FEHLER: $Msg" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
if (-not (Test-Path $LpRepo)) { Fail "Repo nicht gefunden: $LpRepo" }
New-Item -ItemType Directory -Force $TEMP_DIR | Out-Null

Step "1 / 3  Quellcode verpacken"
$zipPath = "$TEMP_DIR\lp_update.zip"
Compress-Archive -Path "$LpRepo\src","$LpRepo\requirements.txt","$LpRepo\.env.example" `
    -DestinationPath $zipPath -Force
Ok "ZIP: $([math]::Round((Get-Item $zipPath).Length/1KB,1)) KB"

# Update-Skript auf Proxmox erstellen (Python entpackt Windows-ZIP korrekt)
$updateSh = "$TEMP_DIR\lp_update.sh"
@"
#!/bin/bash
set -e

# ZIP in LXC pushen
pct push $LxcId /tmp/lp_update.zip /tmp/lp_update.zip

# In LXC entpacken: src/ ersetzen, pycache leeren, Service neu starten
pct exec $LxcId -- bash -c '
python3 -c "
import zipfile, os, shutil

# Alten src-Ordner entfernen
shutil.rmtree(\"/opt/loopingpilot/src\", ignore_errors=True)

z = zipfile.ZipFile(\"/tmp/lp_update.zip\")
for m in z.namelist():
    name = m.replace(\"\\\\\\\\\", \"/\")
    dest = os.path.join(\"/opt/loopingpilot\", name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not name.endswith(\"/\"):
        with open(dest, \"wb\") as f:
            f.write(z.read(m))
print(\"Entpackt:\", len(z.namelist()), \"Eintraege\")
"
find /opt/loopingpilot -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
systemctl restart loopingpilot
sleep 3
systemctl status loopingpilot --no-pager | head -8
'
echo "FERTIG"
"@ | Set-Content -Encoding UTF8 -Path $updateSh
# BOM entfernen
$bytes = [System.IO.File]::ReadAllBytes($updateSh)
if ($bytes[0] -eq 0xEF) { [System.IO.File]::WriteAllBytes($updateSh, $bytes[3..($bytes.Length-1)]) }

Step "2 / 3  Upload"
Upload $zipPath "/tmp/lp_update.zip"
Upload $updateSh "/tmp/lp_update.sh"
Ok "Hochgeladen."

Step "3 / 3  Update im LXC ausführen"
Invoke-Prox "bash /tmp/lp_update.sh 2>&1"

Ok "`nUpdate abgeschlossen."
