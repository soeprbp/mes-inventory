# build-homebase.ps1
# Package the HomeBase workstation components into a distribution package

$dest = Join-Path (Split-Path $PSScriptRoot -Parent) "HomeBase\dist"
$rootPath = Split-Path $PSScriptRoot -Parent
$binPath = Join-Path $rootPath "bin"
$serverPath = Join-Path $rootPath "server"

# 1. Clean existing dist folder
if (Test-Path $dest) {
    Remove-Item -Path $dest -Recurse -Force
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null

# 2. Create distribution structure
$toolsPath = Join-Path $dest "tools"
$serverDestPath = Join-Path $dest "server"
$dataPath = Join-Path $dest "data"
New-Item -ItemType Directory -Path $toolsPath -Force | Out-Null
New-Item -ItemType Directory -Path $serverDestPath -Force | Out-Null
New-Item -ItemType Directory -Path $dataPath -Force | Out-Null

# 3. Copy executables from tools/ and HomeBase/
if (Test-Path $binPath) {
    Copy-Item -Path "$binPath\*" -Destination $toolsPath -Recurse -Force
}

# 4. Copy server files (api.py, init_db.py, dashboard)
if (Test-Path $serverPath) {
    $serverFiles = @("api.py", "init_db.py")
    foreach ($file in $serverFiles) {
        $sourceFile = Join-Path $serverPath $file
        if (Test-Path $sourceFile) {
            Copy-Item -Path $sourceFile -Destination $serverDestPath
        }
    }
    
    # Copy dashboard folder if it exists
    $dashboardPath = Join-Path $serverPath "dashboard"
    if (Test-Path $dashboardPath) {
        Copy-Item -Path $dashboardPath -Destination $serverDestPath -Recurse -Force
    }
}

# 5. Copy oui_database.csv, mac_lookup.py from HomeBase/data and HomeBase/tools
$ouiPath = Join-Path $rootPath "HomeBase\data\oui_database.csv"
if (Test-Path $ouiPath) {
    Copy-Item -Path $ouiPath -Destination (Join-Path $dataPath "oui_database.csv") -Force
}
$macLookupPath = Join-Path $rootPath "HomeBase\tools\mac_lookup.py"
if (Test-Path $macLookupPath) {
    Copy-Item -Path $macLookupPath -Destination (Join-Path $toolsPath "mac_lookup.py") -Force
}

# 6. Copy export.py
$exportPath = Join-Path $rootPath "HomeBase\tools\export.py"
if (Test-Path $exportPath) {
    Copy-Item -Path $exportPath -Destination (Join-Path $toolsPath "export.py") -Force
}

# 7. Create run-server.bat (starts Flask API)
$runServerBat = @"
@echo off
echo Starting MES Inventory Server...
cd server
python api.py
pause
"@
Set-Content -Path (Join-Path $dest "run-server.bat") -Value $runServerBat

# 8. Create README.txt
$readmeContent = @"
MES Inventory System - HomeBase Distribution
============================================

This package contains the HomeBase workstation components for the MES Inventory System.

Structure:
- server/         : Flask API server and dashboard
- tools/           : Collection tools and utilities
- data/            : Data storage folder
- export.py        : Data export utility
- oui_database.csv : MAC vendor database
- mac_lookup.py    : MAC address lookup utility

Setup:
1. Run init.bat for first-time setup (installs dependencies, creates database)
2. Run run-server.bat to start the web server
3. Access dashboard at http://localhost:5000

Requirements:
- Python 3.7+
- Flask
- flask-cors

For support, contact the MES team.
"@
Set-Content -Path (Join-Path $dest "README.txt") -Value $readmeContent

# 9. Create init.bat (first-time setup - creates DB, installs dependencies)
$initBat = @"
@echo off
echo MES Inventory HomeBase Setup
echo.
echo Installing dependencies...
pip install flask flask-cors
echo.
echo Initializing database...
cd server
python init_db.py
echo.
echo Setup complete!
echo Run run-server.bat to start the web server.
pause
"@
Set-Content -Path (Join-Path $dest "init.bat") -Value $initBat

# 10. Display final folder size and file count
$files = Get-ChildItem -Path $dest -Recurse -File
$fileCount = $files.Count
$folderSize = ($files | Measure-Object -Property Length -Sum).Sum
$folderSizeMB = [math]::Round($folderSize / 1MB, 2)

Write-Host "===============================================" -ForegroundColor Green
Write-Host "HomeBase Distribution Package Created" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Location: $dest" -ForegroundColor Cyan
Write-Host "Files: $fileCount" -ForegroundColor Cyan
Write-Host "Size: $folderSizeMB MB" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Green
