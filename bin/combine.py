#!/usr/bin/env python3
"""
MES Inventory Combine
Combines collector output and network scan into single JSON file.
"""

import json
import sys
import os
from datetime import datetime
from argparse import ArgumentParser


def combine_data(collector_file: str, netscan_file: str, output_file: str):
    """Combine collector and network scan data"""
    
    print("=" * 50)
    print("MES Inventory Combine")
    print("=" * 50)
    
    # Load collector data
    print(f"\nLoading: {collector_file}")
    with open(collector_file, 'r', encoding='utf-8') as f:
        collector_data = json.load(f)
    
    # Load network scan data
    print(f"Loading: {netscan_file}")
    netscan_data = {"scan_time": None, "discovered_devices": []}
    if os.path.exists(netscan_file):
        with open(netscan_file, 'r', encoding='utf-8') as f:
            netscan_data = json.load(f)
    else:
        print("  (Network scan file not found, skipping)")
    
    # Combine into single structure
    combined = {
        "collection_time": collector_data.get("collection_time", datetime.utcnow().isoformat() + "Z"),
        "scan_time": netscan_data.get("scan_time", ""),
        "hostname": collector_data.get("hostname", "UNKNOWN"),
        "domain": collector_data.get("domain", ""),
        "hardware": collector_data.get("hardware", {}),
        "os": collector_data.get("os", {}),
        "software": collector_data.get("software", []),
        "services": collector_data.get("services", []),
        "network": collector_data.get("network", []),
        "network_scan": {
            "scan_time": netscan_data.get("scan_time", ""),
            "subnets": netscan_data.get("subnets", []),
            "discovered_devices": netscan_data.get("discovered_devices", [])
        },
        "mes_devices_found": len(netscan_data.get("discovered_devices", []))
    }
    
    # Save combined output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)
    
    print(f"\nCombined output saved to: {output_file}")
    print(f"MES devices discovered: {combined['mes_devices_found']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"  Hostname: {combined['hostname']}")
    print(f"  CPU: {combined['hardware'].get('cpu', {}).get('name', 'N/A')}")
    print(f"  RAM: {combined['hardware'].get('ram_gb', 0):.1f} GB")
    print(f"  Software count: {len(combined['software'])}")
    print(f"  Services count: {len(combined['services'])}")
    print(f"  Network adapters: {len(combined['network'])}")
    print(f"  Devices found on network: {len(combined['network_scan']['discovered_devices'])}")


def main():
    parser = ArgumentParser(description="MES Inventory Combine")
    parser.add_argument("--hw", required=True, help="Collector output JSON")
    parser.add_argument("--net", default="network_scan.json", help="Network scan JSON")
    parser.add_argument("--output", "-o", help="Combined output file (auto-generated if not specified)")
    args = parser.parse_args()
    
    # Auto-generate output filename
    if not args.output:
        hostname = "unknown"
        try:
            with open(args.hw, 'r') as f:
                data = json.load(f)
                hostname = data.get('hostname', hostname)
        except:
            pass
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        args.output = f"{hostname}_{timestamp}.json"
    
    combine_data(args.hw, args.net, args.output)


if __name__ == "__main__":
    main()
