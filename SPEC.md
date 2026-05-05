# MES Inventory System - Specification

## Project Overview

**Project Name:** MES Inventory System  
**Purpose:** Automated hardware/software/network inventory collection from Windows machines via USB drive, with automated LLM enrichment and reporting at home base.  
**Target Users:** IT/OT personnel inventorying MES (Manufacturing Execution System) equipment.

---

## System Architecture

### USB Drive Contents
```
MESInventory/
├── bin/
│   ├── collector.exe   # Hardware, OS, Software, Services collection
│   ├── netscan.exe     # Subnet scan + MES device detection
│   └── combine.exe     # Merge outputs into single JSON
├── data/
│   └── inventory/      # Collected JSON files (one per machine)
├── run.bat             # One-shot launcher (manual kickoff)
└── README.txt
```

### Home Base (Workstation) Contents
```
HomeBase/
├── server/
│   ├── server.db       # Master SQLite database
│   ├── api.py          # Flask REST API
│   ├── llm_processor.py # Auto-LLM enrichment (runs after upload, before write)
│   ├── init_db.py      # Database initialization
│   └── dashboard/      # Web UI
│       ├── index.html  # Dashboard
│       ├── assets.html # Asset management
│       └── reports.html # Report builder
├── tools/
│   ├── uploader.exe    # Import USB JSON → staging
│   └── export.py       # CSV/PDF export
└── data/
    ├── staging/        # Imported JSON (pre-LLM processing)
    └── backup/         # Archive of processed JSON
```

---

## Data Flow

```
USB Collection              Home Base (Workstation)
      │                              │
      │  1. collector.exe          │
      │  2. netscan.exe            │
      │  3. combine.exe           │
      │                            │
      ▼                            ▼
  JSON on USB ──────────> uploader.exe
                            │
                            ▼
                      [STAGING]
                            │
                            ▼
                   llm_processor.py  ← Auto-LLM runs here
                   (analyzes JSON,    (extracts additional
                    enriches data)     context from specs)
                            │
                            ▼
                      [server.db]
                            │
                            ▼
                   dashboard / reports
```

---

## Data Collection Scope

| Category | Method | Details |
|----------|--------|---------|
| Hardware | WMI / WMIC fallback | CPU, RAM, BIOS, Disks, Serial, Manufacturer, Model |
| OS | WMI/Registry | Version, build, architecture, install date |
| Software | Registry | Installed programs + versions + publishers |
| Services | WMI / WMIC | Running services, status, start mode |
| Network | WMI | Adapters, IPs, MAC addresses, subnet, gateway, DNS |
| MES Scan | TCP Port Scan | Subnet sweep for industrial protocols |

---

## Network Scanner Details

### Subnet Discovery
- Enumerate active network adapters from WMI
- Extract local IP + subnet mask
- Calculate subnet range
- **Timeout: 2 minutes per subnet**

### ICMP Sweep
- Parallel ping sweep (configurable concurrency)
- 2-second timeout per host

### TCP Port Scan - MES Protocols

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

### MAC Vendor Lookup
- Local OUI database (CSV)
- Fallback: Online lookup if local miss

### Output
- JSON file with discovered devices
- IP, port, detected protocol, MAC vendor

---

## Database Schema

```sql
-- machines: Core device records
CREATE TABLE machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT UNIQUE,
    location TEXT,
    asset_tag TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_sync DATETIME DEFAULT CURRENT_TIMESTAMP,
    llm_analysis TEXT
);

-- hardware: Device specifications
CREATE TABLE hardware (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    cpu TEXT,
    cpu_cores INTEGER,
    cpu_threads INTEGER,
    ram_gb REAL,
    bios_version TEXT,
    bios_manufacturer TEXT,
    serial_number TEXT,
    manufacturer TEXT,
    model TEXT,
    disk_count INTEGER,
    disk_info TEXT,
    chassis_type TEXT
);

-- network: Network configuration
CREATE TABLE network (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    adapter_name TEXT,
    ip_address TEXT,
    mac_address TEXT,
    subnet_mask TEXT,
    gateway TEXT,
    dns_servers TEXT,
    dhcp_enabled INTEGER
);

-- mes_devices: Discovered MES equipment on network
CREATE TABLE mes_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    scan_timestamp DATETIME,
    ip_address TEXT,
    mac_address TEXT,
    port INTEGER,
    protocol TEXT,
    vendor TEXT,
    mac_vendor TEXT,
    service_info TEXT,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- software: Installed programs
CREATE TABLE software (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    name TEXT,
    version TEXT,
    publisher TEXT,
    install_date TEXT
);

-- services: Windows services
CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    name TEXT,
    display_name TEXT,
    status TEXT,
    start_mode TEXT
);
```

---

## Build Components (Go)

All USB binaries are single-file standalone executables compiled with Go.

| Binary | Purpose | Key Libraries |
|--------|---------|---------------|
| collector.exe | WMI queries for hardware/OS/software/services | golang.org/x/sys/windows + go-cim |
| netscan.exe | ICMP sweep + TCP port scan | golang.org/x/net |
| combine.exe | JSON merge | standard library |
| uploader.exe | SQLite insert | modernc.org/sqlite |

---

## LLM Processor (Automated)

Runs automatically after uploader imports JSON to staging, before writing to server.db.

### Process Flow
1. Read imported JSON from staging/
2. Extract hardware specs
3. Query local LLM (OpenCode-CLI) for:
   - Device type identification (e.g., "This appears to be a SCADA server")
   - Likely use case inference
   - MES system detection from services
4. Store LLM analysis in `llm_analysis` field
5. Move JSON to backup/
6. Delete from staging/

### Example LLM Prompts
- "Based on these specs: [hardware JSON], identify this device type and likely purpose"
- "These Windows services are running: [service list]. Which MES platform is likely installed?"

---

## Web Dashboard Features

### Dashboard (index.html)
- Summary statistics (total machines, last scan, MES devices found)
- Recent inventory runs
- Quick links to reports

### Assets (assets.html)
- Paginated list of all inventoried machines
- Search/filter by hostname, location, asset tag
- Edit location and asset_tag fields
- View detailed hardware/software/services history

### Reports (reports.html)
- **Hardware Summary**: CPU/RAM/disk breakdown across fleet
- **Software Inventory**: All installed software across machines
- **MES Coverage**: Machines with MES protocol connections
- **Network Map**: Subnets and discovered devices
- **Export**: CSV, PDF generation

---

## Usage Instructions

### On Target Machine
1. Insert USB drive
2. Double-click `run.bat`
3. Wait for completion (~5-15 minutes depending on network size)
4. Remove USB

### At Home Base
1. Insert USB into workstation with HomeBase
2. Run `tools\uploader.exe`
3. LLM processor runs automatically
4. Access reports via web dashboard

---

## Technical Notes

- All USB binaries must work on Windows 7+ (no PowerShell dependency)
- Use WMIC as fallback if WMI COM fails
- Network scan timeout: 120 seconds per subnet
- Go modules with vendoring for reproducible builds
- SQLite for zero-dependency database

---

## TODO

- [x] Build collector.exe
- [x] Build netscan.exe
- [x] Build combine.exe
- [ ] Build uploader.exe
- [ ] Create database schema (init_db.py)
- [ ] Build Flask API (api.py)
- [ ] Build LLM processor (llm_processor.py)
- [ ] Build web dashboard (HTML/CSS/JS)
- [x] Create run.bat launcher
- [ ] Test on target machines
- [ ] Add OUI database for MAC lookup
