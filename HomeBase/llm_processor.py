#!/usr/bin/env python3
"""
MES Inventory LLM Processor
Automatically enriches inventory data with LLM analysis for device identification.
"""

import json
import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path


def get_paths():
    """Get all necessary paths, works both as script and bundled exe"""
    if getattr(sys, 'frozen', False):
        bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(sys.executable))
        homebase = os.path.dirname(os.path.dirname(bundle_dir))
    else:
        homebase = str(Path(__file__).parent.parent)
    
    server_path = os.path.join(homebase, "server")
    data_path = os.path.join(homebase, "data")
    
    return homebase, server_path, data_path


def get_llm_analysis(hardware_data: dict) -> str:
    """Get LLM analysis of hardware data via OpenCode built-in model"""
    try:
        prompt = (
            f"Based on this hardware inventory data, identify the device type and likely purpose. "
            f"CPU: {hardware_data.get('cpu', {}).get('name', 'Unknown')} "
            f"({hardware_data.get('cpu', {}).get('cores', 0)} cores, {hardware_data.get('cpu', {}).get('threads', 0)} threads). "
            f"RAM: {hardware_data.get('ram_gb', 0)} GB. "
            f"BIOS: {hardware_data.get('bios', {}).get('version', 'Unknown')} "
            f"by {hardware_data.get('bios', {}).get('manufacturer', 'Unknown')}. "
            f"System: {hardware_data.get('manufacturer', 'Unknown')} "
            f"{hardware_data.get('model', 'Unknown')} ({hardware_data.get('chassis_type', 'Unknown')}). "
            f"Serial: {hardware_data.get('serial_number', 'Unknown')}. "
            f"Disks: {hardware_data.get('disk_count', 0)} disks totaling ~"
            f"{sum(d.get('size_gb', 0) for d in hardware_data.get('disks', [])):.1f} GB. "
            f"What type of device is this (workstation, server, laptop, industrial controller, HMI, PLC, etc.) "
            f"and what is its likely purpose in an industrial/MES environment? "
            f"Provide a concise analysis in 1-2 sentences."
        )

        cmd = ["opencode-cli", "run", "--pure", "--dangerously-skip-permissions", "--format", "json", prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return f"LLM analysis error: opencode returned code {result.returncode}"

        # Parse JSON event stream, collect assistant text
        parts = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                if event.get('type') == 'text':
                    text = event.get('part', {}).get('text', '')
                    if text:
                        parts.append(text)
            except json.JSONDecodeError:
                continue
        response = ' '.join(parts).strip()
        if response:
            return response

        return generate_fallback_analysis(hardware_data)

    except subprocess.TimeoutExpired:
        return "LLM analysis error: opencode timed out"
    except FileNotFoundError:
        return "LLM analysis error: opencode-cli not found"
    except Exception as e:
        return f"LLM analysis error: {str(e)}"


def generate_fallback_analysis(hardware_data: dict) -> str:
    """Generate basic analysis without LLM"""
    cpu_name = hardware_data.get('cpu', {}).get('name', '').lower()
    ram_gb = hardware_data.get('ram_gb', 0)
    chassis = hardware_data.get('chassis_type', '').lower()
    manufacturer = hardware_data.get('manufacturer', '').lower()
    model = hardware_data.get('model', '').lower()
    
    # Simple heuristics
    if 'xeon' in cpu_name or ram_gb >= 32:
        device_type = "server"
    elif 'laptop' in chassis or 'notebook' in model:
        device_type = "laptop"
    elif 'ultra' in cpu_name or 'core i7' in cpu_name or 'core i9' in cpu_name:
        device_type = "high-end workstation"
    elif 'atom' in cpu_name or ram_gb <= 4:
        device_type = "low-power device"
    elif 'industrial' in manufacturer or 'industrial' in model:
        device_type = "industrial computer"
    elif 'dell' in manufacturer and ('optiplex' in model or 'latitude' in model):
        device_type = "business workstation"
    elif 'hp' in manufacturer and ('elitedesk' in model or 'prodesk' in model):
        device_type = "business desktop"
    elif 'lenovo' in manufacturer and ('thinkcentre' in model or 'thinkpad' in model):
        device_type = "business computer"
    else:
        device_type = "computer"
    
    purpose_indicators = []
    if ram_gb >= 16:
        purpose_indicators.append("suitable for demanding applications")
    if 'ssd' in str(hardware_data.get('disks', [])).lower():
        purpose_indicators.append("fast storage")
    if ram_gb >= 8 and 'xeon' not in cpu_name:
        purpose_indicators.append("general purpose computing")
    
    purpose = ", ".join(purpose_indicators) if purpose_indicators else "general use"
    
    return f"This appears to be a {device_type} {purpose}."


def process_staging_files(data_path: str) -> int:
    """Process all JSON files in staging area and move to backup"""
    staging_dir = Path(data_path) / "staging"
    backup_dir = Path(data_path) / "backup"
    
    if not staging_dir.exists():
        print("No staging directory found")
        return 0
    
    backup_dir.mkdir(exist_ok=True)
    
    json_files = list(staging_dir.glob("*.json"))
    if not json_files:
        print("No files to process in staging")
        return 0
    
    print(f"Processing {len(json_files)} files with LLM analysis...")
    
    processed = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            hardware_data = data.get('hardware', {})
            llm_analysis = get_llm_analysis(hardware_data)
            data['llm_analysis'] = llm_analysis
            
            backup_file = backup_dir / json_file.name
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            json_file.unlink()
            
            print(f"  Analyzed: {data.get('hostname', 'UNKNOWN')} -> {llm_analysis[:60]}...")
            processed += 1
            
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
    
    return processed


def import_to_database(data_path: str) -> int:
    """Import enriched JSON files from backup into SQLite database"""
    backup_dir = Path(data_path) / "backup"
    if not backup_dir.exists():
        print("No backup directory found")
        return 0

    json_files = list(backup_dir.glob("*.json"))
    if not json_files:
        print("  No files to import")
        return 0

    try:
        sys.path.insert(0, str(Path(__file__).parent / "server"))
        from init_db import add_or_update_machine, init_db

        init_db()
    except ImportError as e:
        print(f"  Database import error: {e}")
        return 0

    imported = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)

            parts = json_file.stem.split('_')
            location = ""
            asset_tag = ""
            if len(parts) >= 4:
                location = parts[1]
                asset_tag = parts[2]
            elif len(parts) >= 3:
                location = parts[1]

            data['location'] = location
            data['asset_tag'] = asset_tag

            machine_id = add_or_update_machine(data)
            print(f"  Imported: {data.get('hostname', 'UNKNOWN')} (ID: {machine_id})")

            archive_dir = Path(data_path) / "archive"
            archive_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = archive_dir / f"{json_file.stem}_{timestamp}{json_file.suffix}"
            shutil.move(str(json_file), str(archive_file))
            imported += 1
        except Exception as e:
            print(f"  Error importing {json_file.name}: {e}")
            error_dir = Path(data_path) / "error"
            error_dir.mkdir(exist_ok=True)
            shutil.move(str(json_file), str(error_dir / json_file.name))

    return imported


def main():
    print("=" * 50)
    print("MES Inventory LLM Processor")
    print("=" * 50)
    
    # Get paths
    homebase, server_path, data_path = get_paths()
    
    print(f"HomeBase: {homebase}")
    print(f"Data path: {data_path}")
    print()
    
    # Step 1: Process staging files with LLM
    processed = process_staging_files(data_path)
    
    # Step 2: Import enriched files into database
    imported = import_to_database(data_path)
    
    print()
    print("=" * 50)
    print(f"LLM processing complete! {processed} files analyzed.")
    print(f"Database import complete! {imported} machines added.")
    print("=" * 50)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
