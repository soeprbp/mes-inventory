import csv
import re
from pathlib import Path

OUI_DB_PATH = Path(__file__).parent.parent / "data" / "oui_database.csv"

def load_oui_database():
    db = {}
    try:
        with open(OUI_DB_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prefix = row.get('prefix', '').upper().replace(':', '').replace('-', '')
                if prefix:
                    db[prefix] = row.get('vendor_name', 'Unknown')
    except FileNotFoundError:
        print(f"Warning: OUI database not found at {OUI_DB_PATH}. MAC vendor lookup disabled.")
    except Exception as e:
        print(f"Warning: Error loading OUI database: {e}. MAC vendor lookup disabled.")
    return db

_oui_db = load_oui_database()

def normalize_mac(mac):
    mac = mac.upper().replace(':', '').replace('-', '')
    return mac[:6]

def lookup_mac(mac_address):
    prefix = normalize_mac(mac_address)
    return _oui_db.get(prefix, "Unknown")
