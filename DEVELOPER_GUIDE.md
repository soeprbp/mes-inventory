# MES Inventory System - Project Status & Developer Guide

**Last Updated:** 2026-05-05
**Git Commit:** `a0a7454`

---

## Project Overview

Automated inventory collection system for MES (Manufacturing Execution System) equipment. USB-based collector runs on target Windows machines, data uploads to SQLite database at home base with LLM-powered device identification and web dashboard for reporting.

---

## Architecture

```
USB Drive (Target Machines)              Home Base (Workstation)
┌────────────────────────────┐           ┌──────────────────────────────┐
│ portable/                  │           │ HomeBase/                    │
│   ├── collector.exe        │           │   server/                    │
│   ├── netscan.exe          │           │     ├── server.db (SQLite)   │
│   ├── combine.exe          │           │     ├── api.py (Flask)       │
│   ├── RunInventory.bat     │           │     └── dashboard/index.html │
│   └── data/inventory/      │──────────>│   tools/                     │
└────────────────────────────┘    USB    │     └── uploader.exe         │
                                         │   llm_processor.exe          │
                                         └──────────────────────────────┘
```

### Data Flow
1. Plug USB into target Windows machine
2. Run `RunInventory.bat` (manual kickoff)
3. `collector.exe` gathers hardware/OS/software/services
4. `netscan.exe` scans subnet for MES protocol devices
5. `combine.exe` merges data into single JSON
6. Bring USB back to home base workstation
7. Run `uploader.exe` to import to SQLite
8. LLM processor enriches data automatically
9. Access dashboard at `http://localhost:5000`

---

## Completed Components

### USB Collection Tools

| File | Description | Status |
|------|-------------|--------|
| `collector.exe` | Hardware/OS/software/services collection via WMI | ✅ Working |
| `netscan.exe` | Network scan + MES protocol detection | ✅ Working |
| `combine.exe` | Merge collector + netscan output | ✅ Working |
| `RunInventory.bat` | One-shot launcher | ✅ Working |

**Source files:** `bin/*.py` (Python scripts)
**Build tool:** PyInstaller 6.20.0
**Dependencies:** wmi, psutil, pywin32

**Tested Output:**
- Hostname: IN016905L
- CPU: Intel Core Ultra 5 235U (12 cores, 14 threads)
- RAM: 31.46 GB
- Software: 247 items
- Services: 328 items
- Network adapters: 1

### Home Base Components

| File | Description | Status |
|------|-------------|--------|
| `init_db.py` | SQLite database schema + helpers | ✅ Complete |
| `api.py` | Flask REST API (6 endpoints) | ✅ Complete |
| `dashboard/index.html` | Web UI with tabs | ✅ Complete |
| `uploader.py` | USB JSON → staging → DB import | ⚠️ Path issue |
| `llm_processor.py` | AI device identification | ✅ Complete |

**Database tables:**
- `machines` - Core device records
- `hardware` - Device specifications
- `network` - Network configuration
- `mes_devices` - Discovered MES equipment
- `software` - Installed programs
- `services` - Windows services

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/machines` | GET | List all machines (?search=, ?limit=) |
| `/api/machines/<id>` | GET | Single machine details |
| `/api/mes-devices` | GET | All MES devices |
| `/api/stats` | GET | Dashboard statistics |
| `/api/software` | GET | All software (?search=) |
| `/api/services` | GET | All services (?search=, ?status=) |
| `/api/export/<format>` | GET | Export CSV/JSON |

---

## Known Issues

### 1. ~~Uploader.exe Path Resolution~~ ✅ FIXED
**Status:** ⚠️ Not working when bundled

**Problem:** When packaged with PyInstaller, the uploader can't find `init_db.py` in the server directory.

**Error:**
```
Error: Server directory not found at C:\Users\soperbp\AppData\Local\server
```

**Root Cause:** The `_MEIPASS` path calculation is incorrect. The uploader is looking in the wrong place when frozen.

**Fix Needed:**
```python
# Current (broken):
homebase = os.path.dirname(os.path.dirname(bundle_dir))

# Should be relative to where the exe is located:
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    homebase = os.path.dirname(exe_dir)  # One level up from tools/
    server_path = os.path.join(homebase, "server")
```

**Workaround:** Run as Python script instead of exe:
```powershell
cd HomeBase/tools
python uploader.py --usb E:\
```

### 2. Network Scan Timeout
- Full scan can take 2+ minutes on large subnets
- `RunInventory.bat` has 120s timeout per subnet
- Works on isolated machines (graceful failure)

### 3. Windows XP Compatibility
- Python 3.13 requires Windows 7+
- For XP support, would need to build with older Python or use Go

---

## Build Instructions

### Prerequisites
```powershell
pip install pyinstaller wmi psutil flask flask-cors
```

### Build All Executables
```powershell
# USB tools
cd bin
python -m PyInstaller --onefile --console --name collector --distpath . collector.py
python -m PyInstaller --onefile --console --name netscan --distpath . netscan.py
python -m PyInstaller --onefile --console --name combine --distpath . combine.py

# HomeBase tools
cd ../HomeBase/tools
python -m PyInstaller --onefile --console --name uploader --distpath . uploader.py

cd ..
python -m PyInstaller --onefile --console --name llm_processor --distpath . llm_processor.py
```

### Run Flask API
```powershell
cd HomeBase/server
python api.py
# Open http://localhost:5000
```

### Initialize Database
```powershell
cd HomeBase/server
python init_db.py
```

---

## Directory Structure

```
mesinventory/
├── SPEC.md                    # Technical specification
├── README.md                  # Project overview
├── DEVELOPER_GUIDE.md         # This file
├── .gitignore                 # Git ignore rules
│
├── bin/                       # USB tool source + built exes
│   ├── collector.py/exe       # System inventory
│   ├── netscan.py/exe         # Network/MES scanner
│   └── combine.py/exe         # JSON merger
│
├── portable/                  # USB-ready package (copy this folder)
│   ├── RunInventory.bat       # One-click launcher
│   ├── collector.exe
│   ├── netscan.exe
│   ├── combine.exe
│   └── README.md
│
└── HomeBase/                  # Workstation components
    ├── server/
    │   ├── server.db           # SQLite database
    │   ├── init_db.py          # Schema + DB helpers
    │   ├── api.py              # Flask REST API
    │   └── dashboard/
    │       └── index.html      # Web UI
    ├── tools/
    │   ├── uploader.py/exe     # USB import tool
    │   └── data/
    │       ├── staging/        # Pre-LLM
    │       ├── backup/         # Post-LLM
    │       ├── archive/        # Imported
    │       └── error/          # Failed imports
    └── llm_processor.py/exe   # AI enrichment
```

---

## TODO

- [x] Fix uploader.exe path resolution
- [ ] Test on target machines
- [ ] Add OUI database for MAC lookup
- [ ] Package homebase for distribution
- [ ] Create deployment scripts
- [ ] Add error handling to network scanner
- [ ] Add export PDF reports
- [ ] Add machine history/change tracking
- [ ] Add error handling to network scanner
- [ ] Add export PDF reports
- [ ] Add machine history/change tracking

---

## Git History

```
a0a7454 Add HomeBase components: database, API, dashboard, LLM processor, uploader
44476dc Add USB collection tools: collector, netscan, combine + portable package
a25eed0 Initial commit: MES Inventory System - project structure and specification
```
