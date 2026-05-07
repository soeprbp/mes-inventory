# MES Inventory System — Complete Rebuild Guide

## Prerequisites

### Home Base (Workstation)
- Windows 10/11
- Python 3.13+ (https://www.python.org/downloads/)
- pip

### Install Dependencies
```powershell
pip install flask flask-cors wmi psutil pywin32 reportlab pyinstaller
```

---

## Step-by-Step Setup

### 1. Clone/Copy Source
```
git clone https://github.com/soeprbp/workdev.git
cd workdev/mes-inventory
```

### 2. Initialize Database
```powershell
cd HomeBase\server
python init_db.py
```

### 3. Configure API Token
Edit `HomeBase/server/config.py`:
```python
MES_API_TOKEN = 'change-me-to-secure-token'
```

### 4. Build USB Executables
```powershell
cd bin
python -m PyInstaller --onefile --console --name collector --distpath . collector.py
python -m PyInstaller --onefile --console --name netscan --distpath . netscan.py
python -m PyInstaller --onefile --console --name combine --distpath . combine.py
```

### 5. Build HomeBase Executables
```powershell
cd ..\HomeBase\tools
python -m PyInstaller --onefile --console --name uploader --distpath . uploader.py

cd ..
python -m PyInstaller --onefile --console --name llm_processor --distpath . llm_processor.py
```

### 6. Run Server
```powershell
cd HomeBase\server
python api.py
# Open http://localhost:5000 in browser
```

---

## Build Distribution Packages

```powershell
# Portable USB package
.\scripts\build-portable.ps1
# Output: portable/MESInventory/

# HomeBase distribution
.\scripts\build-homebase.ps1
# Output: HomeBase\dist\
```

---

## Testing

```powershell
# Health check
curl http://localhost:5000/api/health

# Get machines (requires token)
curl -H "X-API-Token: your-token" http://localhost:5000/api/machines

# Or via query param
curl "http://localhost:5000/api/machines?token=your-token"
```

---

## Data Pipeline

```
USB data/inventory/*.json
    ↓ (uploader.py)
HomeBase/data/staging/
    ↓ (llm_processor.py)
HomeBase/data/backup/
    ↓ (uploader.py)
HomeBase/server/server.db
    ↓ (success)
HomeBase/data/archive/
    ↓ (failure)
HomeBase/data/error/
```

---

## Export Data

```powershell
# CLI export
cd HomeBase\tools
python export.py machines --format csv --output inventory.csv
python export.py software --format pdf

# API export
curl -H "X-API-Token: token" "http://localhost:5000/api/export/csv?type=machines" -o out.csv
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| No module named 'wmi' | `pip install wmi pywin32` |
| No module named 'flask' | `pip install flask flask-cors` |
| Empty software list | Run `RunInventory.bat` as Administrator |
| Network scan finds nothing | Expected on isolated machines |
| Port 5000 in use | `netstat -ano \| findstr :5000` |

---

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

---

## Quick Reference

```powershell
# Full rebuild
pip install flask flask-cors wmi psutil pywin32 reportlab pyinstaller
cd HomeBase\server && python init_db.py
cd bin
python -m PyInstaller --onefile --console --name collector --distpath . collector.py
python -m PyInstaller --onefile --console --name netscan --distpath . netscan.py
python -m PyInstaller --onefile --console --name combine --distpath . combine.py
cd ..\HomeBase\tools
python -m PyInstaller --onefile --console --name uploader --distpath . uploader.py
cd ..
python -m PyInstaller --onefile --console --name llm_processor --distpath . llm_processor.py
cd HomeBase\server
python api.py
```
