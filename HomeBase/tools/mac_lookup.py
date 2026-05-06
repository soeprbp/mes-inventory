import csv
import re
from pathlib import Path

OUI_DB_PATH = Path(__file__).parent.parent / "data" / "oui_database.csv"

def load_oui_database():
    db = {}
    with open(OUI_DB_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prefix = row['prefix'].upper().replace(':', '').replace('-', '')
            db[prefix] = row['vendor_name']
    return db

_oui_db = load_oui_database()

def normalize_mac(mac):
    mac = mac.upper().replace(':', '').replace('-', '')
    return mac[:6]

def lookup_mac(mac_address):
    prefix = normalize_mac(mac_address)
    return _oui_db.get(prefix, "Unknown")
