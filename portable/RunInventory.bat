@echo off
setlocal enabledelayedexpansion

echo ================================================
echo MES Inventory Collection System
echo ================================================
echo.

REM Detect USB drive letter
set USBDRIVE=
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%D:\MESInventory\bin\collector.exe set USBDRIVE=%%D:
)
if not defined USBDRIVE (
    set USBDRIVE=%~dp0
)

echo Using drive: %USBDRIVE%
echo.

REM Change to working directory
cd /d "%USBDRIVE%\MESInventory" 2>nul || cd /d "%USBDRIVE%"

REM Get computer name for output
set COMPUTERNAME=%COMPUTERNAME%
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Create data directory
if not exist "data" mkdir data
if not exist "data\inventory" mkdir data\inventory

echo [%date% %time%] Starting inventory collection...
echo.

REM Step 1: Run collector
echo [Step 1 of 3] Collecting system information...
echo.
bin\collector.exe --output data\system.json
if errorlevel 1 (
    echo ERROR: Collector failed!
    goto :error
)
echo.
echo Collector complete.
echo.

REM Step 2: Run network scan
echo [Step 2 of 3] Scanning network for MES devices...
echo This may take up to 2 minutes...
echo.
bin\netscan.exe --output data\network_scan.json --scan-timeout 120
REM Network scan failure is non-fatal (machine may be isolated)
if errorlevel 1 (
    echo Warning: Network scan encountered issues.
    echo Continuing with local data only...
    echo.
)
echo.
echo Network scan complete.
echo.

REM Step 3: Combine data
echo [Step 3 of 3] Combining data into final inventory...
echo.
bin\combine.exe --hw data\system.json --net data\network_scan.json --output data\inventory\%COMPUTERNAME%_%TIMESTAMP%.json
if errorlevel 1 (
    echo ERROR: Combine failed!
    goto :error
)
echo.

REM Clean up temp files
del data\system.json 2>nul
del data\network_scan.json 2>nul

REM Show summary
echo ================================================
echo Collection Complete!
echo ================================================
echo.
echo Output saved to: data\inventory\%COMPUTERNAME%_%TIMESTAMP%.json
echo.
echo You may now safely remove the USB drive.
echo.
pause
exit /b 0

:error
echo.
echo ================================================
echo An error occurred during collection.
echo ================================================
echo.
pause
exit /b 1
