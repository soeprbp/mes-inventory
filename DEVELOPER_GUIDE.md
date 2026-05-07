# MES Inventory System — Developer Guide

**Last Updated:** 2026-05-06

## Components

| File | Purpose |
|------|---------|
| `bin/collector.py` | Hardware/OS/software/services via WMI |
| `bin/netscan.py` | Subnet scan + MES protocol detection |
| `bin/combine.py` | Merge collector + netscan JSON |
| `HomeBase/server/api.py` | Flask REST API (7 endpoints) |
| `HomeBase/server/init_db.py` | SQLite schema (6 tables) |
| `HomeBase/tools/uploader.py` | USB → staging → LLM → DB |
| `HomeBase/tools/export.py` | CSV/PDF export |
| `HomeBase/llm_processor.py` | AI device identification |
| `HomeBase/tools/mac_lookup.py` | MAC OUI vendor lookup |
| `HomeBase/data/oui_database.csv` | 871 MAC vendor entries |

## API Endpoints

All require `X-API-Token` header or `?token=` param (except `/api/health`):
- `GET /api/health` — Public health check
- `GET /api/machines` — List machines
- `GET /api/machines/<id>` — Machine details
- `GET /api/stats` — Dashboard stats
- `GET /api/software` — Software list
- `GET /api/services` — Services list
- `GET /api/mes-devices` — MES devices
- `GET /api/export/csv?type=` — CSV export
- `GET /api/export/json?type=` — JSON export

## Database Schema (6 Tables)

- `machines` — hostname, location, asset_tag, llm_analysis
- `hardware` — CPU, RAM, BIOS, disks (FK: machines)
- `network` — adapters, IP, MAC, gateway (FK: machines)
- `mes_devices` — IP, port, protocol (FK: machines)
- `software` — name, version, publisher (FK: machines)
- `services` — name, display_name, status (FK: machines)

## Build Instructions

```powershell
pip install flask flask-cors wmi psutil pywin32 reportlab pyinstaller

cd bin
python -m PyInstaller --onefile --console --name collector --distpath . collector.py
python -m PyInstaller --onefile --console --name netscan --distpath . netscan.py
python -m PyInstaller --onefile --console --name combine --distpath . combine.py

cd ..\HomeBase\tools
python -m PyInstaller --onefile --console --name uploader --distpath . uploader.py
```

## Security

- Token auth on all data endpoints (set `MES_API_TOKEN` env var or edit `config.py`)
- Rate limiting: 100 req/min per IP
- XSS prevention: HTML encoding in dashboard
- CSV injection prevention: sanitize `=+-@` prefix
- Debug disabled, localhost only

## MES Protocol Ports

| Port | Protocol | Vendor |
|------|----------|--------|
| 502 | Modbus TCP | Generic |
| 102 | Siemens S7 | Siemens |
| 4840 | OPC-UA | OPC Foundation |
| 44818 | EtherNet/IP | Rockwell/ODVA |
| 1911 | FIPS | Honeywell |
| 9600 | FINS | Omron |
| 8222 | DeltaV | Emerson |
| 50200 | BACnet | ASHRAE |

## Setup

```powershell
cd HomeBase\server
python init_db.py
# Edit config.py → set MES_API_TOKEN
python api.py
# Open http://localhost:5000
```

## Troubleshooting

- **No module named 'wmi'** → `pip install wmi pywin32`
- **Empty software list** → Run as Administrator
- **Network scan finds nothing** → Expected on isolated machines
- **Uploader import error** → Run `python uploader.py --usb E:\` instead of .exe

## Full Rebuild

See **REBUILD.md** for complete step-by-step rebuild from scratch.
