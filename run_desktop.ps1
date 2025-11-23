# Launch Activity Tracker desktop build detached with health check and auto-terminate
param(
  [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$exe = Join-Path $root 'dist/ActivityTracker/ActivityTracker.exe'
if (-not (Test-Path $exe)) {
  Write-Host "Desktop build not found at $exe" -ForegroundColor Red
  Write-Host "Build first:" -ForegroundColor Yellow
  Write-Host "  pyinstaller --noconfirm --onedir --name ActivityTracker --add-data 'templates;templates' --add-data 'static;static' desktop_app.py"
  exit 1
}

# Ensure auto-terminate is on
$env:ACTIVITY_TRACKER_AUTO_TERMINATE = '1'

# Start detached
Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe)

# Wait for server and open browser
$port = $null
for ($i=0; $i -lt 20; $i++) {
  Start-Sleep -Milliseconds 300
  foreach ($p in 5000..5006) {
    try {
      $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$p/health" -UseBasicParsing -TimeoutSec 1
      if ($resp.StatusCode -eq 200) { $port = $p; break }
    } catch { }
  }
  if ($port) { break }
}

if ($port) {
  Write-Host "Activity Tracker is running on http://127.0.0.1:$port/" -ForegroundColor Green
  if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$port/"
  }
} else {
  Write-Host "Could not detect server on ports 5000-5006. Check logs or try again." -ForegroundColor Yellow
}
