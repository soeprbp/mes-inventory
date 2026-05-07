# MES Inventory System

USB-based hardware/software/network inventory collection for factory floor Windows machines.

## Quick Start

### On Target Machine (USB)
1. Copy `portable/MESInventory/` to USB drive
2. Plug into Windows machine
3. Run `RunInventory.bat`
4. Wait 5-15 minutes
5. Remove USB, repeat for next machine

### At Home Base
```powershell
# First time
cd HomeBase\server
python init_db.py
# Edit config.py → set MES_API_TOKEN

# Start server
python api.py

# Import USB data
cd ..\tools
python uploader.py --usb E:\
```

## What It Collects

- **Hardware:** CPU, RAM, BIOS, disks, manufacturer, serial
- **OS:** Version, build, architecture, install date
- **Software:** Installed programs with versions/publishers
- **Services:** Windows services with status
- **Network:** Adapters, IPs, MACs, gateway, DNS
- **MES Devices:** Modbus TCP, S7, OPC-UA, EtherNet/IP, FINS, DeltaV, BACnet

## Architecture

```
USB ─collector.exe─> JSON ─netscan.exe─> JSON ─combine.exe─> JSON
                                                             │
USB ─uploader.py─> staging ─llm_processor.py─> backup ──> database
                                                                  │
API ───> dashboard (http://localhost:5000) <── export.py
```

## Documentation

- `SPEC.md` — Technical specification, database schema
- `DEVELOPER_GUIDE.md` — Build instructions, API reference
- `REBUILD.md` — Complete rebuild from scratch
