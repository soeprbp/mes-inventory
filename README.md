# MES Inventory System

Automated inventory collection system for MES (Manufacturing Execution System) equipment.

## Quick Start

### On Target Machine (USB)
1. Copy `portable/` folder to USB drive
2. Plug into target Windows machine
3. Run `RunInventory.bat`
4. Wait ~5-15 minutes
5. Remove USB

### At Home Base (Workstation)
1. Plug USB into workstation
2. Run `HomeBase/tools/uploader.exe --usb E:\` (replace E: with USB drive)
3. Start API: `cd HomeBase/server && python api.py`
4. Open http://localhost:5000 in browser

## What It Collects

| Component | Details |
|-----------|---------|
| Hardware | CPU, RAM, BIOS, disks, manufacturer, model |
| OS | Windows version, build, architecture, install date |
| Software | Installed programs with versions and publishers |
| Services | Windows services with status |
| Network | Adapters, IP addresses, MAC addresses, gateway, DNS |
| MES Devices | Network scan detecting Modbus, S7, OPC-UA, EtherNet/IP, etc. |

## Documentation

- `SPEC.md` - Technical specification and architecture
- `DEVELOPER_GUIDE.md` - Build instructions, known issues, next steps

## Project Structure

```
portable/           <- USB collection tools
bin/                <- Source code for USB tools
HomeBase/           <- Workstation components
  server/           <- Flask API + database + dashboard
  tools/            <- Uploader for USB import
  llm_processor.py  <- AI device identification
```

## Requirements

- Windows 10/11 (target machines)
- Python 3.13+ (home base)
- PyInstaller (for building executables)

## Status

**Core system:** ✅ Functional
**Known issues:** Uploader.exe path resolution (run as Python script as workaround)
