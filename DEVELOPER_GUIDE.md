# MES Inventory System - Project Status & Developer Guide

**Last Updated:** 2026-05-06
**Git Commit:** `see git log`

---

## Project Overview

Automated inventory collection system for MES (Manufacturing Execution System) equipment. USB-based collector runs on target Windows machines, data uploads to SQLite database at home base with LLM-powered device identification and web dashboard for reporting.

---

## Architecture

```
USB Drive (Target Machines)              Home Base (Workstation)
┌────────────────────────────┐           ┌────────────────────────────────┐
│ portable/MESInventory/     │           │ HomeBase/                      │
│   ├── collector.exe        │           │   server/                      │
│   ├── netscan.exe          │           │     ├── server.db (SQLite)     │
│   ├── combine.exe          │           │     ├── api.py (Flask)         │
│   ├── RunInventory.bat     │           │     └── dashboard/index.html   │
│   └── data/inventory/      │──────────>│   tools/                       │
└────────────────────────────┘    USB    │     ├── uploader.exe           │
                                         │     ├── export.py              │
                                         │     └── mac_lookup.py          │
                                         │   data/                        │
                                         │     └── oui_database.csv       │
                                         │   llm_processor.exe            │
                                         └────────────────────────────────┘
```

### Data Flow
1. Plug USB into target Windows machine
2. Run `RunInventory.bat` (manual kickoff)
3. `collector.exe` gathers hardware/OS/software/services/network
4. `netscan.exe` scans subnet for MES protocol devices
5. `combine.exe` merges data into single JSON
6. Bring USB back to home base workstation
7. Run `uploader.exe` to import to SQLite (staging → LLM → DB)
8. Access dashboard at `http://localhost:5000`
9. Use `export.py` for CSV/PDF reports

---

## Completed Components

### USB Collection Tools

| File | Description | Status |
|------|-------------|--------|
| `collector.exe` | Hardware/OS/software/services/network via WMI | ✅ Working |
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
| `api.py` | Flask REST API (7 endpoints) | ✅ Complete |
| `dashboard/index.html` | Web UI with tabs | ✅ Complete |
| `uploader.py` | USB JSON → staging → LLM → DB import | ✅ Working |
| `llm_processor.py` | AI device identification | ✅ Complete |
| `export.py` | CSV/PDF export (machines, software, services, MES) | ✅ Complete |
| `mac_lookup.py` | MAC address OUI vendor lookup | ✅ Complete |
| `oui_database.csv` | 871 vendor OUI entries | ✅ Complete |

**Database tables:**
- `machines` - Core device records
- `hardware` - Device specifications
- `network` - Network configuration
- `mes_devices` - Discovered MES equipment
- `software` - Installed programs
- `services` - Windows services

### Packaging & Deployment Scripts

| Script | Description | Status |
|--------|-------------|--------|
| `scripts/build-portable.ps1` | Builds USB-ready package | ✅ Complete |
| `scripts/build-homebase.ps1` | Builds HomeBase dist package | ✅ Complete |
| `scripts/init.bat` | First-time HomeBase setup | ✅ Complete |
| `scripts/run-server.bat` | Start Flask API server | ✅ Complete |

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

### Export Tool (`export.py`)

```bash
# Export all machines to CSV
python tools/export.py machines --format csv --output inventory.csv

# Export software to PDF
python tools/export.py software --format pdf

# Export MES devices filtered by hostname
python tools/export.py mes --hostname "server01"

# Export everything
python tools/export.py all
```

---

## Security

### Authentication
All API endpoints require authentication via token. Set the token via:
- Environment variable: `set MES_API_TOKEN=your-secret-token`
- Or edit `server/config.py`

**Using the API:**
- Header: `X-API-Token: your-token`
- Query param: `?token=your-token`

**Health check endpoint** (`/api/health`) does NOT require authentication.

### Implemented Security Features

| Feature | Description |
|---------|-------------|
| Token Authentication | All data endpoints require API token |
| Rate Limiting | 100 requests/minute per IP (30/min for exports) |
| Security Headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS |
| XSS Prevention | Dashboard HTML-encodes all user data |
| CSV Injection Prevention | Formula injection mitigated in all exports |
| Debug Mode Disabled | Hardcoded to False, cannot be enabled |
| Localhost Only | API binds to 127.0.0.1 only |

### Configuration
Edit `server/config.py` for production settings:
```python
MES_API_TOKEN = 'your-secure-token'  # CHANGE THIS!
PORT = 5000
HOST = '127.0.0.1'
```

---

## Known Issues

### 1. ~~Uploader.exe Path Resolution~~ ✅ FIXED
**Status:** ✅ Fixed - uses `sys.executable` path resolution

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
pip install pyinstaller wmi psutil flask flask-cors reportlab
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

### Package for Distribution
```powershell
# Build portable USB package
.\scripts\build-portable.ps1
# Output: portable/MESInventory/

# Build HomeBase distribution
.\scripts\build-homebase.ps1
# Output: HomeBase/dist/
```

### Run Flask API
```powershell
cd HomeBase/server
python api.py
# Open http://localhost:5000
```

### First-Time HomeBase Setup
```powershell
cd HomeBase
.\init.bat
# Or manually:
pip install flask flask-cors
cd server
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
│   └── MESInventory/
│       ├── collector.exe
│       ├── netscan.exe
│       ├── combine.exe
│       ├── RunInventory.bat
│       ├── README.txt
│       └── data/inventory/
│
├── scripts/                   # Build & deployment scripts
│   ├── build-portable.ps1     # Package USB tools
│   ├── build-homebase.ps1     # Package HomeBase dist
│   ├── init.bat               # First-time setup
│   └── run-server.bat         # Start Flask server
│
├── HomeBase/                  # Workstation components
│   ├── server/
│   │   ├── server.db           # SQLite database
│   │   ├── init_db.py          # Schema + DB helpers
│   │   ├── api.py              # Flask REST API
│   │   └── dashboard/
│   │       └── index.html      # Web UI
│   ├── tools/
│   │   ├── uploader.py/exe     # USB import tool
│   │   ├── export.py           # CSV/PDF export utility
│   │   └── mac_lookup.py       # MAC vendor lookup
│   ├── data/
│   │   ├── oui_database.csv    # 871 OUI vendor entries
│   │   ├── staging/            # Pre-LLM
│   │   ├── backup/             # Post-LLM
│   │   ├── archive/            # Imported
│   │   └── error/              # Failed imports
│   └── dist/                  # Distribution package (built)
│       ├── server/
│       ├── tools/
│       ├── data/
│       ├── init.bat
│       ├── run-server.bat
│       └── README.txt
│
├── data/                      # Shared data
├── config/                    # Configuration files
└── src/                       # Source files
```

---

## TODO

- [ ] Test on target MES machines (physical validation required)
- [ ] Add machine history/change tracking between scans
- [ ] Improve network scanner error handling and progress reporting
- [ ] Consider Go rewrite for Windows XP compatibility if needed

---

## Git History

```
see git log for full history
a0a7454 Add HomeBase components: database, API, dashboard, LLM processor, uploader
44476dc Add USB collection tools: collector, netscan, combine + portable package
a25eed0 Initial commit: MES Inventory System - project structure and specification
```
