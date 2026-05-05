# MES Inventory Collection System

## Quick Start
1. Copy this folder to a USB flash drive
2. Plug into the target MES machine
3. Double-click **RunInventory.bat**
4. Wait for completion (~5-15 minutes depending on network size)
5. Remove USB drive

## What It Collects

### System Information
- **Hardware**: CPU, RAM, BIOS, disks, manufacturer, model
- **Operating System**: Version, build, architecture, install date
- **Software**: Installed programs with versions and publishers
- **Services**: Windows services with status
- **Network**: Adapters, IP addresses, MAC addresses, gateway, DNS

### Network Scan
- Scans local subnet for active devices
- Detects MES-style industrial protocol devices:
  - Port 502: Modbus TCP
  - Port 102: Siemens S7
  - Port 4840: OPC-UA
  - Port 44818: EtherNet/IP
  - Port 1911: Honeywell FIPS
  - Port 9600: Omron FINS
  - Port 8222: Emerson DeltaV
  - Port 50200: BACnet

## Output Files

All files are saved to the `data\inventory\` folder on the USB drive:
- `<computername>_<timestamp>.json` - Combined inventory data

## Files Included

| File | Description |
|------|-------------|
| collector.exe | System information collection |
| netscan.exe | Network scanner + MES device detection |
| combine.exe | Combines all data into final JSON |
| RunInventory.bat | One-click launcher |
| data\inventory\ | Output folder |

## Requirements
- Windows 10/11 (Windows 7 compatible with .NET Framework)
- No installation needed - fully portable
- USB drive with ~50MB free space

## Notes
- Network scan may take up to 2 minutes per subnet
- If machine is isolated (no network), scan will skip gracefully
- All data remains on the USB drive - nothing is transmitted
