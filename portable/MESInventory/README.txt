MES Inventory System - Portable Collection Tools
===============================================

This folder contains the portable USB inventory collection tools.

Files:
- collector.exe    : Main inventory collection tool
- netscan.exe      : Network scanner for discovering devices
- combine.exe      : Combines collector and network scan output
- RunInventory.bat : Launches the full inventory collection

Output files:
- output.json      : Hardware/software inventory results
- scan.json        : Network scan results
- <hostname>_<timestamp>.json  : Combined final output

Usage:
1. Run RunInventory.bat to start collection
2. Copy the combined JSON file to your HomeBase data/ directory

For more information, contact the MES team.
