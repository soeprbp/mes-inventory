# build-portable.ps1
# Package the USB collection tools into a ready-to-copy folder

$dest = Join-Path (Split-Path $PSScriptRoot -Parent) "portable"
$binPath = Join-Path (Split-Path $PSScriptRoot -Parent) "mes-inventory\bin"

# 1. Clean existing portable folder
if (Test-Path $dest) {
    Remove-Item -Path $dest -Recurse -Force
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null

# 2. Create MESInventory folder structure
$inventoryPath = Join-Path $dest "MESInventory"
New-Item -ItemType Directory -Path $inventoryPath -Force | Out-Null
$dataPath = Join-Path $inventoryPath "data"
New-Item -ItemType Directory -Path $dataPath -Force | Out-Null
$inventoryDataPath = Join-Path $dataPath "inventory"
New-Item -ItemType Directory -Path $inventoryDataPath -Force | Out-Null

# 3. Copy collector.exe, netscan.exe, combine.exe from ../bin/
$binFiles = @("collector.exe", "netscan.exe", "combine.exe")
foreach ($file in $binFiles) {
    $sourceFile = Join-Path $binPath $file
    if (Test-Path $sourceFile) {
        Copy-Item -Path $sourceFile -Destination $inventoryPath
    } else {
        Write-Warning "File not found: $sourceFile"
    }
}

# 4. Create RunInventory.bat
$runBatContent = @"
@echo off
echo ========================================
echo MES Inventory Collection
echo ========================================
cd /d "%~dp0"

echo [1/3] Running hardware/software collector...
collector.exe --output output.json
if errorlevel 1 (
    echo ERROR: collector.exe failed with code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo [2/3] Running network scanner...
netscan.exe --output scan.json
if errorlevel 1 (
    echo ERROR: netscan.exe failed with code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo [3/3] Combining results...
combine.exe --hw output.json --net scan.json
if errorlevel 1 (
    echo ERROR: combine.exe failed with code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================
echo Collection complete!
echo ========================================
pause
"@
$runBatPath = Join-Path $inventoryPath "RunInventory.bat"
Set-Content -Path $runBatPath -Value $runBatContent

# 5. Create data/inventory folder (already created above)

# 6. Create README.txt
$readmeContent = @"
MES Inventory System - Portable Collection Tools
===============================================

This folder contains the portable USB inventory collection tools.

Files:
- collector.exe    : Main inventory collection tool
- netscan.exe      : Network scanner for discovering devices
- combine.exe      : Combines collector and network scan output
- RunInventory.bat : Launches the full inventory collection

Output files:
- output.json      : Hardware/software inventory results
- scan.json        : Network scan results
- <hostname>_<timestamp>.json  : Combined final output

Usage:
1. Run RunInventory.bat to start collection
2. Copy the combined JSON file to your HomeBase data/ directory

For more information, contact the MES team.
"@
$readmePath = Join-Path $inventoryPath "README.txt"
Set-Content -Path $readmePath -Value $readmeContent

# 7. Display final folder size and file count
$files = Get-ChildItem -Path $inventoryPath -Recurse -File
$fileCount = $files.Count
$folderSize = ($files | Measure-Object -Property Length -Sum).Sum
$folderSizeMB = [math]::Round($folderSize / 1MB, 2)

Write-Host "===============================================" -ForegroundColor Green
Write-Host "Portable Package Created Successfully" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Location: $inventoryPath" -ForegroundColor Cyan
Write-Host "Files: $fileCount" -ForegroundColor Cyan
Write-Host "Size: $folderSizeMB MB" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Green
