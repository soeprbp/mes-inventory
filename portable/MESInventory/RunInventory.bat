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
