#!/usr/bin/env python3
"""
MES Inventory LLM Processor
Automatically enriches inventory data with LLM analysis for device identification.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from pathlib import Path
import sqlite3


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


def get_openai_config():
    """Read OpenAI config from config.py or environment"""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "server"))
        from config import OPENAI_API_KEY, OPENAI_MODEL
        api_key = OPENAI_API_KEY or os.environ.get('OPENAI_API_KEY', '')
        model = OPENAI_MODEL
    except ImportError:
        api_key = os.environ.get('OPENAI_API_KEY', '')
        model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    return api_key, model


def get_llm_analysis(hardware_data: dict) -> str:
    """Get LLM analysis of hardware data via OpenAI API"""
    api_key, model = get_openai_config()
    
    if not api_key:
        return generate_fallback_analysis(hardware_data)
    
    try:
        prompt = f"""Based on this hardware inventory data, identify the device type and likely purpose:

Hardware:
- CPU: {hardware_data.get('cpu', {}).get('name', 'Unknown')} ({hardware_data.get('cpu', {}).get('cores', 0)} cores, {hardware_data.get('cpu', {}).get('threads', 0)} threads)
- RAM: {hardware_data.get('ram_gb', 0)} GB
- BIOS: {hardware_data.get('bios', {}).get('version', 'Unknown')} by {hardware_data.get('bios', {}).get('manufacturer', 'Unknown')}
- System: {hardware_data.get('manufacturer', 'Unknown')} {hardware_data.get('model', 'Unknown')} ({hardware_data.get('chassis_type', 'Unknown')})
- Serial: {hardware_data.get('serial_number', 'Unknown')}
- Disks: {hardware_data.get('disk_count', 0)} disks totaling ~{sum(d.get('size_gb', 0) for d in hardware_data.get('disks', [])):.1f} GB

What type of device is this (workstation, server, laptop, industrial controller, HMI, PLC, etc.) and what is its likely purpose in an industrial/MES environment? Provide a concise analysis in 1-2 sentences."""

        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an industrial IT analyst specializing in MES environment device identification."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.3
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        result = json.loads(resp.read().decode('utf-8'))
        return result['choices'][0]['message']['content'].strip()

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "LLM analysis error: Invalid API key"
        return f"LLM analysis error: HTTP {e.code}"
    except urllib.error.URLError:
        return generate_fallback_analysis(hardware_data)
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


def main():
    print("=" * 50)
    print("MES Inventory LLM Processor")
    print("=" * 50)
    
    # Get paths
    homebase, server_path, data_path = get_paths()
    
    print(f"HomeBase: {homebase}")
    print(f"Data path: {data_path}")
    print()
    
    # Process staging files
    processed = process_staging_files(data_path)
    
    print()
    print("=" * 50)
    print(f"LLM processing complete! {processed} files analyzed.")
    print("=" * 50)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
