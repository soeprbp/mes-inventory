# MES Inventory System

Automated inventory collection from Windows machines via USB drive.

## Quick Start

### On Target Machine
1. Insert USB
2. Run `run.bat`
3. Wait for completion
4. Remove USB

### At Home Base
1. Plug USB into workstation
2. Run `HomeBase\tools\uploader.exe`
3. Open `HomeBase\server\api.py` in browser or use dashboard

## Directory Structure

```
MESInventory/          <- USB contents
  bin/                 <- Collection binaries
  data/inventory/      <- Collected data
  run.bat              <- One-shot launcher

HomeBase/              <- Home base workstation
  server/              <- Flask API + dashboard
  tools/               <- Uploader + export tools
  data/                <- Staging + backup
```

## Requirements

- Windows 7+
- USB drive with write access

## For Development

See SPEC.md for full technical specification.
