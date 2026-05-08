#!/usr/bin/env python3
"""
MES Inventory Uploader
Imports inventory JSON files from USB to staging area at home base.
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from argparse import ArgumentParser

def get_paths():
    """Get all necessary paths, works both as script and bundled exe"""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        # Use sys.executable to find the actual exe location (not _MEIPASS temp dir)
        exe_dir = os.path.dirname(sys.executable)
        # Structure: homebase/tools/uploader.exe
        # So homebase is one level up from tools/
        homebase = os.path.dirname(exe_dir)
    else:
        # Running as script
        homebase = str(Path(__file__).parent.parent)
    
    server_path = os.path.join(homebase, "server")
    tools_path = os.path.join(homebase, "tools")
    data_path = os.path.join(homebase, "data")
    
    return homebase, server_path, tools_path, data_path

# Get paths
homebase, server_path, tools_path, data_path = get_paths()

# Add server directory to path for imports
sys.path.insert(0, server_path)

try:
    from init_db import get_db, add_or_update_machine
except ImportError as e:
    print(f"Error importing init_db: {e}")
    print(f"Server path: {server_path}")
    print(f"Sys path: {sys.path[:3]}...")
    if os.path.exists(server_path):
        print(f"Server contents: {os.listdir(server_path)}")
    else:
        print("Server directory does not exist")
    sys.exit(1)


def validate_inventory_json(data: dict) -> bool:
    """Validate that the imported JSON has the minimum required fields"""
    if not isinstance(data, dict):
        raise ValueError("Invalid data: expected a JSON object")
    
    if 'hostname' not in data or not data.get('hostname'):
        raise ValueError("Missing required field: 'hostname'")
    
    # hostname must be a string
    if not isinstance(data['hostname'], str):
        raise ValueError("'hostname' must be a string")
    
    # Validate hardware if present
    hw = data.get('hardware', {})
    if hw and not isinstance(hw, dict):
        raise ValueError("'hardware' must be a JSON object")
    
    # Validate collections are lists if present
    for field in ['software', 'services', 'network']:
        if field in data and not isinstance(data[field], list):
            raise ValueError(f"'{field}' must be a JSON array")
    
    return True


def scan_usb_json_files(usb_path: str) -> list:
    """Scan USB drive for inventory JSON files"""
    inventory_dir = Path(usb_path) / "data" / "inventory"
    if not inventory_dir.exists():
        print(f"No inventory directory found at {inventory_dir}")
        return []
    
    json_files = list(inventory_dir.glob("*.json"))
    print(f"Found {len(json_files)} inventory files on USB")
    return json_files


def import_json_to_staging(json_file: Path, staging_dir: Path) -> bool:
    """Copy JSON file from USB to staging area"""
    try:
        # Create staging filename with timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        stem = json_file.stem
        staging_file = staging_dir / f"{stem}_{timestamp}.json"
        
        shutil.copy2(json_file, staging_file)
        print(f"  Copied: {json_file.name} -> {staging_file.name}")
        return True
    except Exception as e:
        print(f"  Error copying {json_file.name}: {e}")
        return False


def process_staging_files(staging_dir: Path) -> int:
    """Process all JSON files in staging area using LLM enrichment"""
    print("\nProcessing staging files...")
    
    # Import LLM processor
    llm_processor_path = Path(homebase) / "llm_processor.py"
    if not llm_processor_path.exists():
        print("  LLM processor not found - skipping enrichment")
        json_files = list(staging_dir.glob("*.json"))
        for json_file in json_files:
            backup_dir = Path(data_path) / "backup"
            backup_dir.mkdir(exist_ok=True)
            shutil.move(str(json_file), str(backup_dir / json_file.name))
            print(f"  Moved to backup (no enrichment): {json_file.name}")
        return len(json_files)
    
    # Run LLM processor
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(llm_processor_path)],
            cwd=homebase,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            print("  LLM processing completed")
            # Count processed files
            backup_dir = Path(data_path) / "backup"
            processed = len(list(backup_dir.glob("*.json"))) if backup_dir.exists() else 0
            return processed
        else:
            print(f"  LLM processor failed: {result.stderr}")
            return 0
    except subprocess.TimeoutExpired:
        print("  LLM processor timed out")
        return 0
    except Exception as e:
        print(f"  Error running LLM processor: {e}")
        return 0


def import_to_database(staging_dir: Path) -> int:
    """Import processed JSON files from backup to database"""
    print("\nImporting to database...")
    
    backup_dir = Path(data_path) / "backup"
    if not backup_dir.exists():
        print("  No backup directory found")
        return 0
    
    json_files = list(backup_dir.glob("*.json"))
    if not json_files:
        print("  No files to import")
        return 0
    
    imported = 0
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            # Validate JSON schema before importing
            try:
                validate_inventory_json(data)
            except ValueError as ve:
                print(f"  Validation failed for {json_file.name}: {ve}")
                error_dir = Path(data_path) / "error"
                error_dir.mkdir(exist_ok=True)
                shutil.move(str(json_file), str(error_dir / json_file.name))
                continue
            
            # Extract location/asset tag from filename if possible
            # Format: hostname_YYYYMMDD_HHMMSS.json or hostname_location_tag_timestamp.json
            parts = json_file.stem.split('_')
            location = ""
            asset_tag = ""
            
            if len(parts) >= 4:
                # Assume format: hostname_location_tag_timestamp
                location = parts[1]
                asset_tag = parts[2]
            elif len(parts) >= 3:
                # Assume format: hostname_location_timestamp
                location = parts[1]
            
            data['location'] = location
            data['asset_tag'] = asset_tag
            
            # Add to database
            machine_id = add_or_update_machine(data)
            print(f"  Imported: {data.get('hostname', 'UNKNOWN')} (ID: {machine_id})")
            
            # Move to archive with timestamp
            archive_dir = Path(data_path) / "archive"
            archive_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = archive_dir / f"{json_file.stem}_{timestamp}{json_file.suffix}"
            shutil.move(str(json_file), str(archive_file))
            
            imported += 1
        except Exception as e:
            print(f"  Error importing {json_file.name}: {e}")
            # Move to error folder
            error_dir = Path(data_path) / "error"
            error_dir.mkdir(exist_ok=True)
            shutil.move(str(json_file), str(error_dir / json_file.name))
    
    return imported


def main():
    parser = ArgumentParser(description="MES Inventory Uploader")
    parser.add_argument("--usb", "-u", default=".", help="USB drive path (default: current directory)")
    parser.add_argument("--staging", "-s", default="staging", help="Staging directory (default: data/staging)")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM enrichment")
    args = parser.parse_args()
    
    print("=" * 50)
    print("MES Inventory Uploader")
    print("=" * 50)
    print(f"USB path: {args.usb}")
    print(f"Staging: {args.staging}")
    print()
    
    # Setup paths
    usb_path = Path(args.usb).resolve()
    
    # Determine staging directory
    if args.staging == "staging":
        staging_dir = Path(data_path) / "staging"
    else:
        staging_dir = Path(args.staging)
    staging_dir.mkdir(exist_ok=True)
    
    # Step 1: Scan USB for JSON files
    print("[1/4] Scanning USB for inventory files...")
    json_files = scan_usb_json_files(str(usb_path))
    if not json_files:
        print("No inventory files found on USB. Nothing to do.")
        return 0
    
    # Step 2: Copy to staging
    print("\n[2/4] Copying files to staging area...")
    copied = 0
    for json_file in json_files:
        if import_json_to_staging(json_file, staging_dir):
            copied += 1
    
    if copied == 0:
        print("No files copied successfully.")
        return 1
    
    print(f"\nCopied {copied}/{len(json_files)} files to staging.")
    
    # Step 3: Process with LLM (unless skipped)
    if not args.skip_llm:
        print("\n[3/4] Processing with LLM enrichment...")
        processed = process_staging_files(staging_dir)
        print(f"Processed {processed} files.")
    else:
        print("\n[3/4] Skipping LLM enrichment (--skip-llm flag)")
        # Just move files to backup for import
        backup_dir = Path(data_path) / "backup"
        backup_dir.mkdir(exist_ok=True)
        moved = 0
        for json_file in staging_dir.glob("*.json"):
            shutil.move(str(json_file), str(backup_dir / json_file.name))
            moved += 1
        print(f"Moved {moved} files to backup.")
    
    # Step 4: Import to database
    print("\n[4/4] Importing to database...")
    imported = import_to_database(staging_dir)
    
    print("\n" + "=" * 50)
    print(f"Import complete! {imported} machines added to database.")
    print("=" * 50)
    
    return 0 if imported > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
