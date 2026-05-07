#!/usr/bin/env python3
"""
MES Inventory Flask API
Provides REST endpoints for accessing inventory data.
"""

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, request, g, make_response
from flask_cors import CORS
from pathlib import Path

# Import database functions
import sys
server_path = str(Path(__file__).parent)
sys.path.append(server_path)
from init_db import get_db, get_all_machines, get_machine_by_id, get_mes_devices

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Security: Get API token from environment or config file
try:
    from config import MES_API_TOKEN, DEBUG_MODE
    SERVER_PORT = int(os.environ.get('PORT', 5000))
    if DEBUG_MODE:
        print("WARNING: Debug mode enabled - not for production!")
except ImportError:
    # Fallback to environment variables
    MES_API_TOKEN = os.environ.get('MES_API_TOKEN', 'changeme-in-production')
    DEBUG_MODE = False
    SERVER_PORT = int(os.environ.get('PORT', 5000))

# Rate limiting: Simple in-memory counter (per IP)
from collections import defaultdict
from time import time
rate_limit_hits = defaultdict(list)

def rate_limit(max_requests=100, window_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            now = time()
            
            # Clean old entries
            rate_limit_hits[client_ip] = [
                t for t in rate_limit_hits[client_ip] 
                if now - t < window_seconds
            ]
            
            if len(rate_limit_hits[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            rate_limit_hits[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def require_auth(f):
    """Simple token-based authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-API-Token') or request.args.get('token', '')
        
        if not token or token != MES_API_TOKEN:
            return jsonify({'error': 'Authentication required. Provide X-API-Token header or ?token='}), 401
        
        return f(*args, **kwargs)
    return decorated

def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.after_request
def after_request(response):
    """Apply security headers to all responses"""
    return add_security_headers(response)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'server.db'))
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_csv_value(value):
    """Prevent CSV formula injection"""
    if value is None:
        return ''
    str_value = str(value)
    # Prefix cells starting with =, +, -, @, \t, \r, \n with single quote
    if str_value.startswith(('=', '+', '-', '@')) or str_value.startswith(('\t', '\r', '\n')):
        return "'" + str_value
    return str_value

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint (no auth required)"""
    return jsonify({'status': 'ok', 'version': '1.0.0'})

@app.route('/api/machines', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_machines():
    """Get list of all machines with optional search"""
    search = request.args.get('search', '').lower()
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    conn = get_db_connection()
    try:
        if search:
            query = '''
                SELECT m.*, 
                       GROUP_CONCAT(DISTINCT s.name) as software_names,
                       COUNT(DISTINCT s.id) as software_count
                FROM machines m
                LEFT JOIN software s ON m.id = s.machine_id
                WHERE LOWER(m.hostname) LIKE ? 
                   OR LOWER(m.location) LIKE ? 
                   OR LOWER(m.asset_tag) LIKE ?
                GROUP BY m.id
                ORDER BY m.hostname
            '''
            search_term = f'%{search}%'
            machines = conn.execute(query, (search_term, search_term, search_term)).fetchall()
        else:
            machines = conn.execute('SELECT * FROM machines ORDER BY hostname').fetchall()
        
        # Apply pagination
        if limit is not None:
            machines = machines[offset:offset+limit]
        elif offset > 0:
            machines = machines[offset:]
        
        # Convert to dict and add counts
        result = []
        for machine in machines:
            m_dict = dict(machine)
            # Get counts
            hw_count = conn.execute('SELECT COUNT(*) FROM hardware WHERE machine_id = ?', (m_dict['id'],)).fetchone()[0]
            net_count = conn.execute('SELECT COUNT(*) FROM network WHERE machine_id = ?', (m_dict['id'],)).fetchone()[0]
            sw_count = conn.execute('SELECT COUNT(*) FROM software WHERE machine_id = ?', (m_dict['id'],)).fetchone()[0]
            svc_count = conn.execute('SELECT COUNT(*) FROM services WHERE machine_id = ?', (m_dict['id'],)).fetchone()[0]
            mes_count = conn.execute('SELECT COUNT(*) FROM mes_devices WHERE machine_id = ?', (m_dict['id'],)).fetchone()[0]
            
            m_dict['counts'] = {
                'hardware': hw_count,
                'network': net_count,
                'software': sw_count,
                'services': svc_count,
                'mes_devices': mes_count
            }
            result.append(m_dict)
        
        return jsonify(result)
    finally:
        conn.close()

@app.route('/api/machines/<int:machine_id>', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_machine(machine_id):
    """Get detailed information for a specific machine"""
    conn = get_db_connection()
    try:
        machine = conn.execute('SELECT * FROM machines WHERE id = ?', (machine_id,)).fetchone()
        if not machine:
            return jsonify({'error': 'Machine not found'}), 404
        
        m_dict = dict(machine)
        
        # Get related data
        m_dict['hardware'] = conn.execute('SELECT * FROM hardware WHERE machine_id = ?', (machine_id,)).fetchone()
        m_dict['hardware'] = dict(m_dict['hardware']) if m_dict['hardware'] else None
        
        m_dict['network'] = [dict(row) for row in conn.execute('SELECT * FROM network WHERE machine_id = ?', (machine_id,)).fetchall()]
        m_dict['software'] = [dict(row) for row in conn.execute('SELECT * FROM software WHERE machine_id = ?', (machine_id,)).fetchall()]
        m_dict['services'] = [dict(row) for row in conn.execute('SELECT * FROM services WHERE machine_id = ?', (machine_id,)).fetchall()]
        m_dict['mes_devices'] = [dict(row) for row in conn.execute('SELECT * FROM mes_devices WHERE machine_id = ? ORDER BY last_seen DESC', (machine_id,)).fetchall()]
        
        # Add counts
        m_dict['counts'] = {
            'hardware': 1 if m_dict['hardware'] else 0,
            'network': len(m_dict['network']),
            'software': len(m_dict['software']),
            'services': len(m_dict['services']),
            'mes_devices': len(m_dict['mes_devices'])
        }
        
        return jsonify(m_dict)
    finally:
        conn.close()

@app.route('/api/mes-devices', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_all_mes_devices():
    """Get all discovered MES devices across all machines"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    conn = get_db_connection()
    try:
        query = '''
            SELECT md.*, m.hostname, m.location
            FROM mes_devices md
            JOIN machines m ON md.machine_id = m.id
            ORDER BY md.last_seen DESC
        '''
        devices = conn.execute(query).fetchall()
        
        # Apply pagination
        if limit is not None:
            devices = devices[offset:offset+limit]
        elif offset > 0:
            devices = devices[offset:]
        
        result = [dict(device) for device in devices]
        return jsonify(result)
    finally:
        conn.close()

@app.route('/api/stats', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_stats():
    """Get dashboard statistics"""
    conn = get_db_connection()
    try:
        stats = {}
        
        # Machine counts
        stats['total_machines'] = conn.execute('SELECT COUNT(*) FROM machines').fetchone()[0]
        stats['machines_today'] = conn.execute(
            "SELECT COUNT(*) FROM machines WHERE DATE(last_seen) = DATE('now')"
        ).fetchone()[0]
        
        # Software counts
        stats['total_software'] = conn.execute('SELECT COUNT(DISTINCT name) FROM software').fetchone()[0]
        stats['unique_software'] = conn.execute('SELECT COUNT(DISTINCT name || version) FROM software').fetchone()[0]
        
        # Service counts
        stats['total_services'] = conn.execute('SELECT COUNT(*) FROM services').fetchone()[0]
        stats['running_services'] = conn.execute("SELECT COUNT(*) FROM services WHERE status = 'Running'").fetchone()[0]
        
        # MES device counts
        stats['total_mes_devices'] = conn.execute('SELECT COUNT(*) FROM mes_devices').fetchone()[0]
        stats['unique_mes_protocols'] = conn.execute('SELECT COUNT(DISTINCT protocol) FROM mes_devices WHERE protocol IS NOT NULL').fetchone()[0]
        
        # Network info
        stats['total_network_adapters'] = conn.execute('SELECT COUNT(*) FROM network').fetchone()[0]
        
        # Recent activity
        stats['recent_machines'] = conn.execute(
            '''SELECT hostname, last_seen FROM machines 
               ORDER BY datetime(last_seen) DESC LIMIT 5'''
        ).fetchall()
        stats['recent_machines'] = [dict(row) for row in stats['recent_machines']]
        
        return jsonify(stats)
    finally:
        conn.close()

@app.route('/api/software', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_software():
    """Get list of all software across machines"""
    search = request.args.get('search', '').lower()
    limit = request.args.get('limit', type=int)
    
    conn = get_db_connection()
    try:
        if search:
            query = '''
                SELECT name, version, publisher, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as installed_on
                FROM software s
                JOIN machines m ON s.machine_id = m.id
                WHERE LOWER(name) LIKE ? OR LOWER(publisher) LIKE ? OR LOWER(version) LIKE ?
                GROUP BY name, version, publisher
                ORDER BY install_count DESC, name
            '''
            search_term = f'%{search}%'
            software = conn.execute(query, (search_term, search_term, search_term)).fetchall()
        else:
            query = '''
                SELECT name, version, publisher, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as installed_on
                FROM software s
                JOIN machines m ON s.machine_id = m.id
                GROUP BY name, version, publisher
                ORDER BY install_count DESC, name
            '''
            software = conn.execute(query).fetchall()
        
        if limit is not None:
            software = software[:limit]
        
        result = []
        for sw in software:
            sw_dict = dict(sw)
            sw_dict['installed_on_list'] = sw_dict['installed_on'].split(',') if sw_dict['installed_on'] else []
            result.append(sw_dict)
        
        return jsonify(result)
    finally:
        conn.close()

@app.route('/api/services', methods=['GET'])
@rate_limit(max_requests=100, window_seconds=60)
@require_auth
def get_services():
    """Get list of all services across machines"""
    search = request.args.get('search', '').lower()
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    try:
        if search and status:
            query = '''
                SELECT name, display_name, status, start_mode, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as running_on
                FROM services s
                JOIN machines m ON s.machine_id = m.id
                WHERE LOWER(name) LIKE ? OR LOWER(display_name) LIKE ? 
                AND s.status = ?
                GROUP BY name, display_name, status, start_mode
                ORDER BY install_count DESC, name
            '''
            search_term = f'%{search}%'
            services = conn.execute(query, (search_term, search_term, status)).fetchall()
        elif search:
            query = '''
                SELECT name, display_name, status, start_mode, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as running_on
                FROM services s
                JOIN machines m ON s.machine_id = m.id
                WHERE LOWER(name) LIKE ? OR LOWER(display_name) LIKE ? OR LOWER(status) LIKE ?
                GROUP BY name, display_name, status, start_mode
                ORDER BY install_count DESC, name
            '''
            search_term = f'%{search}%'
            services = conn.execute(query, (search_term, search_term, search_term)).fetchall()
        elif status:
            query = '''
                SELECT name, display_name, status, start_mode, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as running_on
                FROM services s
                JOIN machines m ON s.machine_id = m.id
                WHERE s.status = ?
                GROUP BY name, display_name, status, start_mode
                ORDER BY install_count DESC, name
            '''
            services = conn.execute(query, (status,)).fetchall()
        else:
            query = '''
                SELECT name, display_name, status, start_mode, COUNT(*) as install_count,
                       GROUP_CONCAT(DISTINCT m.hostname) as running_on
                FROM services s
                JOIN machines m ON s.machine_id = m.id
                GROUP BY name, display_name, status, start_mode
                ORDER BY install_count DESC, name
            '''
            services = conn.execute(query).fetchall()
        
        result = []
        for svc in services:
            svc_dict = dict(svc)
            svc_dict['running_on_list'] = svc_dict['running_on'].split(',') if svc_dict['running_on'] else []
            result.append(svc_dict)
        
        return jsonify(result)
    finally:
        conn.close()

@app.route('/api/export/<format>', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
@require_auth
def export_data(format):
    """Export data in various formats"""
    export_type = request.args.get('type', 'machines')  # machines, software, services, mes
    
    if format not in ['csv', 'json']:
        return jsonify({'error': 'Unsupported format. Use csv or json'}), 400
    
    conn = get_db_connection()
    try:
        if export_type == 'machines':
            data = conn.execute('SELECT * FROM machines ORDER BY hostname').fetchall()
            fields = [description[0] for description in conn.description]
        elif export_type == 'software':
            data = conn.execute('''
                SELECT s.*, m.hostname as machine_name
                FROM software s
                JOIN machines m ON s.machine_id = m.id
                ORDER BY s.name
            ''').fetchall()
            fields = [description[0] for description in conn.description]
        elif export_type == 'services':
            data = conn.execute('''
                SELECT s.*, m.hostname as machine_name
                FROM services s
                JOIN machines m ON s.machine_id = m.id
                ORDER BY s.name
            ''').fetchall()
            fields = [description[0] for description in conn.description]
        elif export_type == 'mes':
            data = conn.execute('''
                SELECT md.*, m.hostname, m.location
                FROM mes_devices md
                JOIN machines m ON md.machine_id = m.id
                ORDER BY md.last_seen DESC
            ''').fetchall()
            fields = [description[0] for description in conn.description]
        else:
            return jsonify({'error': 'Invalid export type'}), 400
        
        if format == 'json':
            result = [dict(row) for row in data]
            return jsonify(result)
        else:  # CSV - sanitize to prevent formula injection
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([sanitize_csv_value(f) for f in fields])
            for row in data:
                writer.writerow([sanitize_csv_value(row[field]) for field in fields])
            
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv; charset=utf-8',
                'Content-Disposition': f'attachment; filename={export_type}_{datetime.now().strftime("%Y%m%d")}.csv'
            }
    finally:
        conn.close()

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Security: Always disabled, binds to localhost only
    app.run(host='127.0.0.1', port=SERVER_PORT, debug=False)
