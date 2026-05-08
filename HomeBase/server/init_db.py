import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostname TEXT UNIQUE,
                location TEXT,
                asset_tag TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_sync DATETIME DEFAULT CURRENT_TIMESTAMP,
                llm_analysis TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hardware (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
                cpu TEXT,
                cpu_cores INTEGER,
                cpu_threads INTEGER,
                ram_gb REAL,
                bios_version TEXT,
                bios_manufacturer TEXT,
                serial_number TEXT,
                manufacturer TEXT,
                model TEXT,
                disk_count INTEGER,
                disk_info TEXT,
                chassis_type TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
                adapter_name TEXT,
                ip_address TEXT,
                mac_address TEXT,
                subnet_mask TEXT,
                gateway TEXT,
                dns_servers TEXT,
                dhcp_enabled INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mes_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
                scan_timestamp DATETIME,
                ip_address TEXT,
                mac_address TEXT,
                port INTEGER,
                protocol TEXT,
                vendor TEXT,
                mac_vendor TEXT,
                service_info TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS software (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
                name TEXT,
                version TEXT,
                publisher TEXT,
                install_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
                name TEXT,
                display_name TEXT,
                status TEXT,
                start_mode TEXT
            )
        ''')
        
        conn.commit()
        print(f"Database initialized at {DB_PATH}")

def add_or_update_machine(data_dict):
    with get_db() as conn:
        cursor = conn.cursor()
        
        hostname = data_dict.get('hostname')
        
        cursor.execute('SELECT id FROM machines WHERE hostname = ?', (hostname,))
        existing = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if existing:
            machine_id = existing['id']
            cursor.execute('''
                UPDATE machines SET
                    location = COALESCE(?, location),
                    asset_tag = COALESCE(?, asset_tag),
                    last_seen = ?,
                    last_sync = ?
                WHERE id = ?
            ''', (
                data_dict.get('location'),
                data_dict.get('asset_tag'),
                now,
                now,
                machine_id
            ))
        else:
            cursor.execute('''
                INSERT INTO machines (hostname, location, asset_tag, first_seen, last_seen, last_sync)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                hostname,
                data_dict.get('location'),
                data_dict.get('asset_tag'),
                now,
                now,
                now
            ))
            machine_id = cursor.lastrowid
        
        if 'hardware' in data_dict:
            hw = data_dict['hardware']
            
            # Handle nested cpu dict from collector
            cpu_data = hw.get('cpu', {})
            if isinstance(cpu_data, dict):
                cpu_name = cpu_data.get('name', '')
                cpu_cores = cpu_data.get('cores', 0)
                cpu_threads = cpu_data.get('threads', 0)
            else:
                cpu_name = cpu_data
                cpu_cores = hw.get('cpu_cores', 0)
                cpu_threads = hw.get('cpu_threads', 0)
            
            # Handle disk_info: serialize list of disks to JSON string
            disks = hw.get('disks', [])
            if isinstance(disks, list):
                import json
                disk_info = json.dumps(disks)
                disk_count = len(disks)
            else:
                disk_info = str(disks) if disks else ''
                disk_count = hw.get('disk_count', 0)
            
            # Get serial from bios or hardware level
            bios_data = hw.get('bios', {})
            if isinstance(bios_data, dict):
                bios_version = bios_data.get('version', '')
                bios_manufacturer = bios_data.get('manufacturer', '')
                bios_serial = bios_data.get('serial_number', '')
            else:
                bios_version = bios_data
                bios_manufacturer = hw.get('bios_manufacturer', '')
                bios_serial = hw.get('bios_serial', '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO hardware 
                (machine_id, cpu, cpu_cores, cpu_threads, ram_gb, bios_version, bios_manufacturer,
                 serial_number, manufacturer, model, disk_count, disk_info, chassis_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (machine_id, cpu_name, cpu_cores, cpu_threads,
                  hw.get('ram_gb', 0), bios_version, bios_manufacturer,
                  bios_serial or hw.get('serial_number', ''),
                  hw.get('manufacturer', ''), hw.get('model', ''),
                  disk_count, disk_info, hw.get('chassis_type', '')))
        
        if 'network' in data_dict:
            for net in data_dict['network']:
                cursor.execute('''
                    INSERT OR REPLACE INTO network
                    (machine_id, adapter_name, ip_address, mac_address, subnet_mask, gateway, dns_servers, dhcp_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (machine_id, net.get('adapter_name'), net.get('ip_address'), net.get('mac_address'),
                      net.get('subnet_mask'), net.get('gateway'), net.get('dns_servers'), net.get('dhcp_enabled')))
        
        if 'software' in data_dict:
            cursor.execute('DELETE FROM software WHERE machine_id = ?', (machine_id,))
            for sw in data_dict['software']:
                cursor.execute('''
                    INSERT INTO software (machine_id, name, version, publisher, install_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (machine_id, sw.get('name'), sw.get('version'), sw.get('publisher'), sw.get('install_date')))
        
        if 'services' in data_dict:
            cursor.execute('DELETE FROM services WHERE machine_id = ?', (machine_id,))
            for svc in data_dict['services']:
                cursor.execute('''
                    INSERT INTO services (machine_id, name, display_name, status, start_mode)
                    VALUES (?, ?, ?, ?, ?)
                ''', (machine_id, svc.get('name'), svc.get('display_name'), svc.get('status'), svc.get('start_mode')))
        
        conn.commit()
        return machine_id

def get_all_machines():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM machines ORDER BY hostname')
        return [dict(row) for row in cursor.fetchall()]

def get_machine_by_id(machine_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM machines WHERE id = ?', (machine_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        machine = dict(row)
        
        cursor.execute('SELECT * FROM hardware WHERE machine_id = ?', (machine_id,))
        hw = cursor.fetchone()
        machine['hardware'] = dict(hw) if hw else None
        
        cursor.execute('SELECT * FROM network WHERE machine_id = ?', (machine_id,))
        machine['network'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM software WHERE machine_id = ?', (machine_id,))
        machine['software'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM services WHERE machine_id = ?', (machine_id,))
        machine['services'] = [dict(row) for row in cursor.fetchall()]
        
        return machine

def get_mes_devices(machine_id=None):
    with get_db() as conn:
        cursor = conn.cursor()
        if machine_id:
            cursor.execute('SELECT * FROM mes_devices WHERE machine_id = ? ORDER BY last_seen DESC', (machine_id,))
        else:
            cursor.execute('SELECT * FROM mes_devices ORDER BY last_seen DESC')
        return [dict(row) for row in cursor.fetchall()]

def main():
    print(f"Initializing MES Inventory Database...")
    print(f"Database path: {DB_PATH}")
    init_db()
    print("Database ready!")

if __name__ == '__main__':
    main()