import argparse
import csv
import sqlite3
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))
from init_db import get_db


def sanitize_csv_value(value):
    """Prevent CSV formula injection attacks"""
    if value is None:
        return ''
    str_value = str(value)
    # Prefix cells starting with =, +, -, @, tab, CR, LF with single quote
    if str_value.startswith(('=', '+', '-', '@')) or str_value.startswith(('\t', '\r', '\n')):
        return "'" + str_value
    return str_value


def export_machines_csv(conn, output_file, hostname_filter=None):
    cursor = conn.cursor()

    query = '''
        SELECT m.hostname, m.location, m.asset_tag, h.cpu, h.ram_gb,
               m.first_seen, m.last_seen
        FROM machines m
        LEFT JOIN hardware h ON m.id = h.machine_id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')

    query += ' ORDER BY m.hostname'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([sanitize_csv_value(h) for h in ['hostname', 'location', 'asset_tag', 'cpu', 'ram_gb', 'first_seen', 'last_seen']])
        for row in rows:
            writer.writerow([sanitize_csv_value(v) for v in row])

    print(f'Exported {len(rows)} machines to {output_file}')


def export_software_csv(conn, output_file, hostname_filter=None):
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, s.name, s.version, s.publisher, s.install_date
        FROM software s
        JOIN machines m ON s.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, s.name'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([sanitize_csv_value(h) for h in ['hostname', 'name', 'version', 'publisher', 'install_date']])
        for row in rows:
            writer.writerow([sanitize_csv_value(v) for v in row])
    
    print(f'Exported {len(rows)} software entries to {output_file}')


def export_services_csv(conn, output_file, hostname_filter=None):
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, s.name, s.display_name, s.status, s.start_mode
        FROM services s
        JOIN machines m ON s.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, s.name'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([sanitize_csv_value(h) for h in ['hostname', 'name', 'display_name', 'status', 'start_mode']])
        for row in rows:
            writer.writerow([sanitize_csv_value(v) for v in row])
    
    print(f'Exported {len(rows)} services entries to {output_file}')


def export_mes_csv(conn, output_file, hostname_filter=None):
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, md.ip_address, md.port, md.protocol, md.vendor, md.mac_vendor, md.last_seen
        FROM mes_devices md
        JOIN machines m ON md.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, md.ip_address'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([sanitize_csv_value(h) for h in ['hostname', 'ip_address', 'port', 'protocol', 'vendor', 'mac_vendor', 'last_seen']])
        for row in rows:
            writer.writerow([sanitize_csv_value(v) for v in row])
    
    print(f'Exported {len(rows)} MES devices to {output_file}')


def export_machines_pdf(conn, output_file, hostname_filter=None):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        print('reportlab not installed. Install with: pip install reportlab')
        sys.exit(1)

    cursor = conn.cursor()

    query = '''
        SELECT m.hostname, m.location, m.asset_tag, h.cpu, h.ram_gb,
               m.first_seen, m.last_seen
        FROM machines m
        LEFT JOIN hardware h ON m.id = h.machine_id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')

    query += ' ORDER BY m.hostname'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Machine Inventory Export', styles['Title']))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))

    data = [['Hostname', 'Location', 'Asset Tag', 'CPU', 'RAM (GB)', 'First Seen', 'Last Seen']]
    for row in rows:
        data.append(list(row))

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)

    print(f'Exported {len(rows)} machines to {output_file}')


def export_software_pdf(conn, output_file, hostname_filter=None):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        print('reportlab not installed. Install with: pip install reportlab')
        sys.exit(1)
    
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, s.name, s.version, s.publisher, s.install_date
        FROM software s
        JOIN machines m ON s.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, s.name'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph('Software Inventory Export', styles['Title']))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    
    data = [['Hostname', 'Name', 'Version', 'Publisher', 'Install Date']]
    for row in rows:
        data.append(list(row))
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    print(f'Exported {len(rows)} software entries to {output_file}')


def export_services_pdf(conn, output_file, hostname_filter=None):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        print('reportlab not installed. Install with: pip install reportlab')
        sys.exit(1)
    
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, s.name, s.display_name, s.status, s.start_mode
        FROM services s
        JOIN machines m ON s.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, s.name'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph('Services Inventory Export', styles['Title']))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    
    data = [['Hostname', 'Name', 'Display Name', 'Status', 'Start Mode']]
    for row in rows:
        data.append(list(row))
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    print(f'Exported {len(rows)} services entries to {output_file}')


def export_mes_pdf(conn, output_file, hostname_filter=None):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        print('reportlab not installed. Install with: pip install reportlab')
        sys.exit(1)
    
    cursor = conn.cursor()
    
    query = '''
        SELECT m.hostname, md.ip_address, md.port, md.protocol, md.vendor, md.mac_vendor, md.last_seen
        FROM mes_devices md
        JOIN machines m ON md.machine_id = m.id
    '''
    params = []
    if hostname_filter:
        query += ' WHERE m.hostname LIKE ?'
        params.append(f'%{hostname_filter}%')
    
    query += ' ORDER BY m.hostname, md.ip_address'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    doc = SimpleDocTemplate(output_file, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph('MES Devices Export', styles['Title']))
    elements.append(Paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', styles['Normal']))
    
    data = [['Hostname', 'IP Address', 'Port', 'Protocol', 'Vendor', 'MAC Vendor', 'Last Seen']]
    for row in rows:
        data.append(list(row))
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    print(f'Exported {len(rows)} MES devices to {output_file}')


def main():
    parser = argparse.ArgumentParser(description='MES Inventory System Export Tool')
    parser.add_argument('command', choices=['machines', 'software', 'services', 'mes', 'all'],
                        help='Export command')
    parser.add_argument('--format', choices=['csv', 'pdf'], default='csv',
                        help='Output format (default: csv)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path (default: export.csv or export.pdf)')
    parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite database (default: ../server/server.db)')
    parser.add_argument('--hostname', type=str, default=None,
                        help='Filter by hostname')
    
    args = parser.parse_args()
    
    if args.db is None:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'server.db')
    else:
        db_path = args.db
    
    if not os.path.exists(db_path):
        print(f'Database not found: {db_path}')
        sys.exit(1)
    
    if args.output is None:
        args.output = f'export.{args.format}'
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if args.command == 'machines' or args.command == 'all':
                if args.format == 'csv':
                    export_machines_csv(conn, args.output if args.command != 'all' else f'machines.{args.format}', args.hostname)
                else:
                    export_machines_pdf(conn, args.output if args.command != 'all' else f'machines.{args.format}', args.hostname)
            
            if args.command == 'software' or args.command == 'all':
                output = args.output if args.command != 'all' else f'software.{args.format}'
                if args.format == 'csv':
                    export_software_csv(conn, output, args.hostname)
                else:
                    export_software_pdf(conn, output, args.hostname)
            
            if args.command == 'services' or args.command == 'all':
                output = args.output if args.command != 'all' else f'services.{args.format}'
                if args.format == 'csv':
                    export_services_csv(conn, output, args.hostname)
                else:
                    export_services_pdf(conn, output, args.hostname)
            
            if args.command == 'mes' or args.command == 'all':
                output = args.output if args.command != 'all' else f'mes.{args.format}'
                if args.format == 'csv':
                    export_mes_csv(conn, output, args.hostname)
                else:
                    export_mes_pdf(conn, output, args.hostname)
    
    except sqlite3.Error as e:
        print(f'Database error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
