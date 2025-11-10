# Build and Package Script for Activity Tracker v1.0.0
# Creates a complete distribution package ready for release

# Create release directory
New-Item -ItemType Directory -Force -Path ".\release\ActivityTracker-v1.0.0" | Out-Null
New-Item -ItemType Directory -Force -Path ".\release\ActivityTracker-v1.0.0\instance" | Out-Null
New-Item -ItemType Directory -Force -Path ".\release\ActivityTracker-v1.0.0\logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\release\ActivityTracker-v1.0.0\backups" | Out-Null

# Copy the built application
Write-Host "Copying executable and dependencies..." -ForegroundColor Cyan
Copy-Item -Path ".\dist\ActivityTracker\*" -Destination ".\release\ActivityTracker-v1.0.0\" -Recurse -Force

# Copy documentation
Write-Host "Copying documentation..." -ForegroundColor Cyan
Copy-Item -Path "RELEASE_NOTES.md" -Destination ".\release\ActivityTracker-v1.0.0\README.txt" -Force
Copy-Item -Path "AUDIT_REPORT.md" -Destination ".\release\ActivityTracker-v1.0.0\AUDIT_REPORT.txt" -Force

# Create a version info file
Write-Host "Creating version file..." -ForegroundColor Cyan
$versionInfo = @"
Activity Tracker v1.0.0
Release Date: November 8, 2025
Build Type: Production (Standalone)
Platform: Windows 10/11 (64-bit)

This is the first official release of Activity Tracker.
See README.txt for installation and usage instructions.
"@
$versionInfo | Out-File -FilePath ".\release\ActivityTracker-v1.0.0\VERSION.txt" -Encoding UTF8

# Create a quick start guide
Write-Host "Creating quick start guide..." -ForegroundColor Cyan
$quickStart = @"
QUICK START GUIDE
=================

1. Double-click ActivityTracker.exe to launch
2. The application will open in your default web browser
3. Start tracking activities using the + button
4. Your data is saved in the instance\ folder

IMPORTANT: Keep all files together in this folder!

For full documentation, see README.txt

Activity Tracker v1.0.0
"@
$quickStart | Out-File -FilePath ".\release\ActivityTracker-v1.0.0\QUICK_START.txt" -Encoding UTF8

# Get folder size
$size = (Get-ChildItem -Path ".\release\ActivityTracker-v1.0.0" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Location: .\release\ActivityTracker-v1.0.0" -ForegroundColor Yellow
Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Yellow
Write-Host "`nTo create ZIP archive, run:" -ForegroundColor Cyan
Write-Host "Compress-Archive -Path '.\release\ActivityTracker-v1.0.0' -DestinationPath '.\release\ActivityTracker-v1.0.0-Windows.zip' -Force" -ForegroundColor White
Write-Host "`n========================================" -ForegroundColor Green
