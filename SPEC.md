# MES Inventory System — Technical Specification

## Project Overview
USB-based automated hardware/software/network inventory collection for MES equipment on factory floor. No installation on target machines.

## Architecture

### USB Collection Tools
```
portable/MESInventory/
├── collector.exe    # Hardware/OS/software/services collection
├── netscan.exe      # Subnet scan for MES protocols
├── combine.exe     # Merge outputs to single JSON
├── RunInventory.bat # One-shot launcher
└── data/inventory/  # Collected JSON files
```

### HomeBase Workstation
```
HomeBase/
├── server/
│   ├── server.db    # SQLite master database
│   ├── api.py       # Flask REST API
│   ├── init_db.py   # Database schema + helpers
│   └── dashboard/
│       └── index.html # Web dashboard
├── tools/
│   ├── uploader.py  # USB import + LLM + DB
│   ├── export.py    # CSV/PDF export
│   └── mac_lookup.py # MAC vendor lookup
├── data/
│   ├── oui_database.csv # 871 OUI entries
│   ├── staging/     # Pre-LLM
│   ├── backup/      # Post-LLM
│   ├── archive/     # Imported
│   └── error/       # Failed
└── llm_processor.py # AI device identification
```

## Data Collection

| Category | Method | Details |
|----------|--------|---------|
| Hardware | WMI | CPU, RAM, BIOS, disks, serial, model |
| OS | WMI/Registry | Version, build, architecture |
| Software | Registry | Installed programs |
| Services | WMI | Status, start mode |
| Network | WMI | Adapters, IPs, MACs, gateway, DNS |
| MES Scan | TCP Port Scan | Industrial protocols |

## Database Schema

```sql
machines (id, hostname, location, asset_tag, first_seen, last_seen, llm_analysis)
hardware (machine_id FK, cpu, cpu_cores, ram_gb, bios_*, serial_number, manufacturer, model, disk_*)
network (machine_id FK, adapter_name, ip_address, mac_address, subnet_mask, gateway, dns_servers, dhcp_enabled)
mes_devices (machine_id FK, scan_timestamp, ip_address, mac_address, port, protocol, vendor, mac_vendor)
software (machine_id FK, name, version, publisher, install_date)
services (machine_id FK, name, display_name, status, start_mode)
```

## Build Components

- **collector.exe** — WMI queries via `golang.org/x/sys/windows` or `wmi` Python package
- **netscan.exe** — ICMP sweep + TCP port scan via `golang.org/x/net` or `socket` + `concurrent.futures`
- **combine.exe** — JSON merge (standard library)
- **uploader.exe** — SQLite insert via `modernc.org/sqlite`

## LLM Processor (Automated)
1. Read JSON from staging/
2. Extract hardware specs
3. Query local LLM (OpenCode-CLI) or heuristic fallback
4. Store analysis in `llm_analysis` field
5. Move JSON to backup/

## Web Dashboard
- Dashboard: Summary stats, recent runs
- Machines: List + search + filter
- Software: Cross-machine inventory
- MES Devices: Protocol discovery results
- Reports: CSV/PDF export

## Build Status

- [x] collector.exe
- [x] netscan.exe
- [x] combine.exe
- [x] uploader.py
- [x] init_db.py
- [x] api.py
- [x] llm_processor.py
- [x] Dashboard (index.html)
- [x] RunInventory.bat
- [x] OUI database (871 entries)
- [x] export.py
- [x] build-portable.ps1
- [x] build-homebase.ps1
- [ ] Test on target MES machines (physical validation)
