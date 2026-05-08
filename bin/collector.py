#!/usr/bin/env python3
"""
MES Inventory Collector
Collects hardware, OS, software, services, and network information from Windows machines.
Outputs JSON for later processing.
"""

import json
import os
import sys
import socket
import uuid
import subprocess
import re
from datetime import datetime
from argparse import ArgumentParser

try:
    import wmi
    import psutil
    HAS_WMI = True
except ImportError:
    HAS_WMI = False


class InventoryCollector:
    def __init__(self):
        self.data = {
            "collection_time": datetime.utcnow().isoformat() + "Z",
            "hostname": socket.gethostname(),
            "domain": "",
            "hardware": {},
            "os": {},
            "software": [],
            "services": [],
            "network": []
        }

    def run_wmic(self, query):
        """Fallback using WMIC command"""
        try:
            # Split query into arguments for safe subprocess call (no shell=True)
            # WMIC format: "path win32_processor get Name /format:csv"
            args = ['wmic'] + query.split()
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            return ""

    def collect_all(self):
        """Collect all inventory data"""
        print("[1/5] Collecting hardware information...")
        self.collect_hardware()

        print("[2/5] Collecting OS information...")
        self.collect_os()

        print("[3/5] Collecting installed software...")
        self.collect_software()

        print("[4/5] Collecting services...")
        self.collect_services()

        print("[5/5] Collecting network configuration...")
        self.collect_network()

        return self.data

    def collect_hardware(self):
        """Collect CPU, RAM, BIOS, Disks, System info"""
        hw = {
            "cpu": {},
            "ram_gb": 0,
            "bios": {},
            "disks": [],
            "manufacturer": "",
            "model": "",
            "chassis_type": "",
            "serial_number": ""
        }

        try:
            # CPU info
            cpu_info = {}
            if HAS_WMI:
                w = wmi.WMI()
                for cpu in w.Win32_Processor():
                    cpu_info = {
                        "name": cpu.Name or "Unknown",
                        "cores": cpu.NumberOfCores or 0,
                        "threads": cpu.NumberOfLogicalProcessors or 0,
                        "max_speed_mhz": int(cpu.MaxClockSpeed or 0)
                    }
            else:
                # Fallback: use WMIC
                output = self.run_wmic("path win32_processor get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:csv")
                lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                if len(lines) > 1:
                    parts = lines[-1].split(',')
                    if len(parts) >= 4:
                        cpu_info = {
                            "name": parts[0] or "Unknown",
                            "cores": int(parts[1]) if parts[1].isdigit() else 0,
                            "threads": int(parts[2]) if parts[2].isdigit() else 0,
                            "max_speed_mhz": int(parts[3]) if parts[3].strip().isdigit() else 0
                        }
                if not cpu_info:
                    cpu_info = {"name": "Unknown", "cores": 0, "threads": 0, "max_speed_mhz": 0}

            hw["cpu"] = cpu_info

            # RAM
            if HAS_WMI:
                mem = 0
                for cs in w.Win32_ComputerSystem():
                    mem = float(cs.TotalPhysicalMemory or 0) / (1024**3)
                hw["ram_gb"] = round(mem, 2)
            else:
                try:
                    mem = psutil.virtual_memory()
                    hw["ram_gb"] = round(mem.total / (1024**3), 2)
                except:
                    hw["ram_gb"] = 0

            # BIOS
            bios_info = {}
            if HAS_WMI:
                for bios in w.Win32_BIOS():
                    bios_info = {
                        "version": bios.SMBIOSBIOSVersion or "",
                        "manufacturer": bios.Manufacturer or "",
                        "serial_number": bios.SerialNumber or ""
                    }
            else:
                output = self.run_wmic("path win32_bios get SMBIOSBIOSVersion,Manufacturer,SerialNumber /format:csv")
                lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                if len(lines) > 1:
                    parts = lines[-1].split(',')
                    if len(parts) >= 3:
                        bios_info = {
                            "version": parts[0] or "",
                            "manufacturer": parts[1] or "",
                            "serial_number": parts[2] or ""
                        }
                if not bios_info:
                    bios_info = {"version": "", "manufacturer": "", "serial_number": ""}

            hw["bios"] = bios_info

            # Disks
            disks = []
            if HAS_WMI:
                for disk in w.Win32_DiskDrive():
                    size_gb = int(disk.Size or 0) / (1024**3)
                    disks.append({
                        "model": disk.Model or "",
                        "size_gb": round(size_gb, 2),
                        "interface_type": disk.InterfaceType or "",
                        "serial_number": disk.SerialNumber or ""
                    })
            else:
                output = self.run_wmic("path win32_diskdrive get Model,Size,InterfaceType /format:csv")
                lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                for line in lines[1:]:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        size = int(parts[1]) if parts[1].strip().isdigit() else 0
                        disks.append({
                            "model": parts[0] or "",
                            "size_gb": round(size / (1024**3), 2),
                            "interface_type": parts[2] or "",
                            "serial_number": ""
                        })

            hw["disks"] = disks

            # System info
            if HAS_WMI:
                for cs in w.Win32_ComputerSystem():
                    hw["manufacturer"] = cs.Manufacturer or ""
                    hw["model"] = cs.Model or ""
                    hw["chassis_type"] = cs.SystemType or ""
                for bios in w.Win32_BIOS():
                    hw["serial_number"] = bios.SerialNumber or ""
            else:
                output = self.run_wmic("path win32_computersystem get Manufacturer,Model /format:csv")
                lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                if len(lines) > 1:
                    parts = lines[-1].split(',')
                    if len(parts) >= 2:
                        hw["manufacturer"] = parts[0] or ""
                        hw["model"] = parts[1] or ""

        except Exception as e:
            print(f"  Warning: Hardware collection error: {e}")

        self.data["hardware"] = hw

    def collect_os(self):
        """Collect OS information"""
        os_info = {
            "name": "",
            "version": "",
            "build": "",
            "architecture": "",
            "install_date": "",
            "hostname": socket.gethostname(),
            "domain": ""
        }

        try:
            if HAS_WMI:
                w = wmi.WMI()
                for opsys in w.Win32_OperatingSystem():
                    os_info["name"] = opsys.Caption or ""
                    os_info["version"] = opsys.Version or ""
                    os_info["build"] = opsys.BuildNumber or ""
                    os_info["architecture"] = opsys.OSArchitecture or ""
                    if opsys.InstallDate:
                        # Parse CIM datetime
                        install = str(opsys.InstallDate)[:8]
                        os_info["install_date"] = f"{install[:4]}-{install[4:6]}-{install[6:8]}"
                    os_info["domain"] = opsys.Domain or ""
                for cs in w.Win32_ComputerSystem():
                    os_info["domain"] = cs.Domain or ""
            else:
                output = self.run_wmic("path win32_operatingsystem get Caption,Version,BuildNumber,OSArchitecture /format:csv")
                lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
                if len(lines) > 1:
                    parts = lines[-1].split(',')
                    if len(parts) >= 4:
                        os_info["name"] = parts[0] or ""
                        os_info["version"] = parts[1] or ""
                        os_info["build"] = parts[2] or ""
                        os_info["architecture"] = parts[3] or ""

                # Get domain via environment (safer than subprocess with shell=True)
                os_info["domain"] = os.environ.get('USERDOMAIN', '')

        except Exception as e:
            print(f"  Warning: OS collection error: {e}")

        self.data["domain"] = os_info["domain"]
        self.data["os"] = os_info

    def collect_software(self):
        """Collect installed software from registry"""
        software = []

        try:
            import winreg

            def get_installedsoftware(hive, path):
                found = []
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            i += 1

                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if name and not name.startswith("Microsoft") or True:  # Include all
                                    version = ""
                                    publisher = ""
                                    install_date = ""

                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] or ""
                                    except:
                                        pass
                                    try:
                                        publisher = winreg.QueryValueEx(subkey, "Publisher")[0] or ""
                                    except:
                                        pass
                                    try:
                                        date_raw = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                        if date_raw and len(date_raw) == 8:
                                            install_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:8]}"
                                    except:
                                        pass

                                    found.append({
                                        "name": name,
                                        "version": str(version),
                                        "publisher": str(publisher),
                                        "install_date": install_date
                                    })
                            except:
                                pass
                            winreg.CloseKey(subkey)
                        except:
                            break
                    winreg.CloseKey(key)
                except:
                    pass
                return found

            # 64-bit software
            software += get_installedsoftware(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
            # 32-bit software on 64-bit Windows
            software += get_installedsoftware(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            # Current user
            software += get_installedsoftware(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

        except Exception as e:
            print(f"  Warning: Software collection error: {e}")

        self.data["software"] = software

    def collect_services(self):
        """Collect Windows services"""
        services = []

        try:
            if HAS_WMI:
                w = wmi.WMI()
                for svc in w.Win32_Service():
                    services.append({
                        "name": svc.Name or "",
                        "display_name": svc.DisplayName or "",
                        "status": svc.State or "",
                        "start_mode": svc.StartMode or ""
                    })
            else:
                # Fallback using sc query
                result = subprocess.run(['sc', 'query', 'state=', 'all'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                current = {}
                for line in lines:
                    line = line.strip()
                    if line.startswith("SERVICE_NAME:"):
                        current["name"] = line.split(":", 1)[1].strip()
                    elif "DISPLAY_NAME:" in line:
                        current["display_name"] = line.split(":", 1)[1].strip()
                    elif "STATE" in line:
                        parts = line.split(":")[1].strip().split(" ")
                        current["status"] = parts[0] if parts else ""
                    elif "WIN32_EXIT_CODE" in line and current.get("name"):
                        services.append({
                            "name": current.get("name", ""),
                            "display_name": current.get("display_name", ""),
                            "status": current.get("status", ""),
                            "start_mode": ""
                        })
                        current = {}

        except Exception as e:
            print(f"  Warning: Services collection error: {e}")

        self.data["services"] = services

    def collect_network(self):
        """Collect network adapter information"""
        adapters = []

        try:
            if HAS_WMI:
                w = wmi.WMI()
                for adapter in w.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                    ip = adapter.IPAddress[0] if adapter.IPAddress else ""
                    mac = adapter.MACAddress or ""
                    subnet = adapter.IPSubnet[0] if adapter.IPSubnet else ""
                    gateway = adapter.DefaultIPGateway[0] if adapter.DefaultIPGateway else ""
                    dns = ",".join(adapter.DNSServerSearchOrder) if adapter.DNSServerSearchOrder else ""
                    dhcp = bool(adapter.DHCPEnabled)

                    # Get adapter name
                    for na in w.Win32_NetworkAdapter(DeviceID=adapter.Index, NetEnabled=True):
                        adapter_name = na.Name or ""

                        adapters.append({
                            "adapter_name": adapter_name,
                            "ip_address": ip,
                            "mac_address": mac,
                            "subnet_mask": subnet,
                            "gateway": gateway,
                            "dns_servers": dns,
                            "dhcp_enabled": dhcp
                        })
            else:
                # Fallback using ipconfig
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
                current_adapter = {}
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(" ") and not line.startswith("."):
                        if current_adapter.get("ip_address"):
                            adapters.append(current_adapter)
                        current_adapter = {"adapter_name": line.rstrip(":"), "ip_address": "", "mac_address": "", "subnet_mask": "", "gateway": "", "dns_servers": "", "dhcp_enabled": False}
                    elif "IPv4" in line or "IP Address" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            current_adapter["ip_address"] = parts[1].strip()
                    elif "MAC" in line or "Physical Address" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            current_adapter["mac_address"] = parts[1].strip().replace("-", ":")
                    elif "Subnet" in line or "Subnet Mask" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            current_adapter["subnet_mask"] = parts[1].strip()
                    elif "Default Gateway" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            current_adapter["gateway"] = parts[1].strip()
                    elif "DHCP Enabled" in line:
                        current_adapter["dhcp_enabled"] = "Yes" in line
                if current_adapter.get("ip_address"):
                    adapters.append(current_adapter)

        except Exception as e:
            print(f"  Warning: Network collection error: {e}")

        self.data["network"] = adapters


def main():
    parser = ArgumentParser(description="MES Inventory Collector")
    parser.add_argument("--output", "-o", default="output.json", help="Output JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 50)
    print("MES Inventory Collector")
    print("=" * 50)

    collector = InventoryCollector()
    data = collector.collect_all()

    # Write output
    output_path = args.output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"\nCollection complete: {output_path}")
    print(f"Software items: {len(data['software'])}")
    print(f"Services: {len(data['services'])}")
    print(f"Network adapters: {len(data['network'])}")


if __name__ == "__main__":
    main()
