#!/usr/bin/env python3
"""
MES Network Scanner
Scans subnets for MES-style industrial protocol devices.
Detects: Modbus, S7, OPC-UA, EtherNet/IP, and more.
"""

import json
import socket
import struct
import time
import concurrent.futures
import subprocess
from datetime import datetime
from argparse import ArgumentParser
from typing import List, Dict, Optional

# MES Protocol Ports
MES_PORTS = {
    502: ("Modbus TCP", "Generic"),
    102: ("Siemens S7", "Siemens"),
    4840: ("OPC-UA", "OPC Foundation"),
    44818: ("EtherNet/IP", "Rockwell/ODVA"),
    1911: ("FIPS", "Honeywell"),
    9600: ("FINS", "Omron"),
    8222: ("DeltaV", "Emerson"),
    50200: ("BACnet", "ASHRAE"),
}

# Common MES service keywords to look for in ARP/cache
MES_SERVICE_KEYWORDS = [
    "opc", "ua", "server", "simatic", "s7", "plc", "modbus",
    "Kepware", "Wonderware", "FactoryTalk", "rslinx", "unity",
    "controllogix", "compactlogix", "plc-5", "slc", "micrologix"
]


class NetworkScanner:
    def __init__(self, timeout: float = 2.0, scan_timeout: int = 120):
        self.timeout = timeout
        self.scan_timeout = scan_timeout
        self.discovered_devices = []
        
    def get_local_subnets(self) -> List[Dict]:
        """Get active network adapters and their subnets"""
        subnets = []
        
        try:
            # Use psutil to get network interfaces
            import psutil
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        netmask = addr.netmask
                        if ip and netmask and not ip.startswith("127."):
                            # Calculate network range
                            ip_int = self._ip_to_int(ip)
                            mask_int = self._ip_to_int(netmask)
                            network_int = ip_int & mask_int
                            broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)
                            
                            subnets.append({
                                "interface": interface,
                                "ip": ip,
                                "netmask": netmask,
                                "network": self._int_to_ip(network_int),
                                "broadcast": self._int_to_ip(broadcast_int),
                                "first_host": self._int_to_ip(network_int + 1),
                                "last_host": self._int_to_ip(broadcast_int - 1),
                                "cidr": self._netmask_to_cidr(netmask)
                            })
        except ImportError:
            # Fallback using ipconfig
            subnets = self._get_subnets_fallback()
            
        return subnets
    
    def _get_subnets_fallback(self) -> List[Dict]:
        """Fallback using ipconfig"""
        subnets = []
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            current_adapter = None
            current_ip = None
            current_mask = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith(" ") and not ":" in line:
                    current_adapter = line
                elif "IPv4" in line or "IP Address" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        current_ip = parts[1].strip()
                elif "Subnet" in line or "Mask" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        current_mask = parts[1].strip()
                        if current_ip and current_mask and not current_ip.startswith("127."):
                            ip_int = self._ip_to_int(current_ip)
                            mask_int = self._ip_to_int(current_mask)
                            network_int = ip_int & mask_int
                            
                            subnets.append({
                                "interface": current_adapter or "Unknown",
                                "ip": current_ip,
                                "netmask": current_mask,
                                "network": self._int_to_ip(network_int),
                                "broadcast": self._int_to_ip(network_int | (~mask_int & 0xFFFFFFFF)),
                                "first_host": self._int_to_ip(network_int + 1),
                                "last_host": self._int_to_ip(network_int | (~mask_int & 0xFFFFFFFF) - 1),
                                "cidr": self._netmask_to_cidr(current_mask)
                            })
                            current_ip = None
                            current_mask = None
        except:
            pass
        return subnets
    
    def _ip_to_int(self, ip: str) -> int:
        return struct.unpack("!I", socket.inet_aton(ip))[0]
    
    def _int_to_ip(self, ip_int: int) -> str:
        return socket.inet_ntoa(struct.pack("!I", ip_int))
    
    def _netmask_to_cidr(self, netmask: str) -> int:
        mask_int = self._ip_to_int(netmask)
        return bin(mask_int).count('1')
    
    def ping_host(self, ip: str) -> bool:
        """Ping a host using Windows ping"""
        try:
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '500', ip],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def tcp_connect(self, ip: str, port: int) -> bool:
        """Try TCP connection to a port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            sock.close()
            return True
        except:
            return False
    
    def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address from ARP cache"""
        try:
            result = subprocess.run(
                ['arp', '-a', ip],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if ip in line:
                    # Parse ARP output
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if '-' in part and len(part) == 17:
                            return part.upper()
        except:
            pass
        return None
    
    def scan_host(self, ip: str, scan_mes_ports: bool = True) -> Optional[Dict]:
        """Scan a single host"""
        device = {
            "ip": ip,
            "mac_address": None,
            "mes_ports": [],
            "services": [],
            "alive": False
        }
        
        # Try ping
        if self.ping_host(ip):
            device["alive"] = True
            device["mac_address"] = self.get_mac_address(ip)
            
            # Scan MES ports
            if scan_mes_ports:
                for port, (protocol, vendor) in MES_PORTS.items():
                    if self.tcp_connect(ip, port):
                        device["mes_ports"].append({
                            "port": port,
                            "protocol": protocol,
                            "vendor": vendor
                        })
        
        return device if device["alive"] or device["mes_ports"] else None
    
    def scan_subnet(self, subnet: Dict, max_workers: int = 50) -> List[Dict]:
        """Scan an entire subnet"""
        print(f"  Scanning {subnet['network']}/{subnet['cidr']} ({subnet['ip']})...")

        devices = []
        start_time = time.time()

        first = self._ip_to_int(subnet['first_host'])
        last = self._ip_to_int(subnet['last_host'])

        if last - first > 254:
            last = first + 254

        ips = [self._int_to_ip(i) for i in range(first, last + 1)]
        print(f"  Scanning {len(ips)} hosts...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.scan_host, ip): ip for ip in ips}

            try:
                for future in concurrent.futures.as_completed(futures, timeout=self.scan_timeout):
                    try:
                        result = future.result()
                        if result and (result["alive"] or result["mes_ports"]):
                            devices.append(result)
                            if result["mes_ports"]:
                                for p in result["mes_ports"]:
                                    print(f"    Found: {result['ip']} - {p['protocol']} ({p['vendor']})")
                    except Exception:
                        pass

                    if time.time() - start_time > self.scan_timeout:
                        print("  Timeout reached, stopping scan...")
                        break
            except concurrent.futures.TimeoutError:
                print("  Timeout reached, stopping scan...")

        elapsed = time.time() - start_time
        print(f"  Scan complete: {len(devices)} devices found in {elapsed:.1f}s")

        return devices
    
    def run_full_scan(self) -> Dict:
        """Run network scan on all active subnets"""
        print("=" * 50)
        print("MES Network Scanner")
        print("=" * 50)
        
        results = {
            "scan_time": datetime.utcnow().isoformat() + "Z",
            "subnets": [],
            "discovered_devices": []
        }
        
        print("\nDetecting local network adapters...")
        subnets = self.get_local_subnets()
        
        if not subnets:
            print("No active network adapters found!")
            return results
        
        print(f"Found {len(subnets)} adapter(s)")
        
        for subnet in subnets:
            print(f"\nSubnet: {subnet['interface']}")
            print(f"  IP: {subnet['ip']}/{subnet['cidr']}")
            
            devices = self.scan_subnet(subnet)
            
            results["subnets"].append(subnet)
            results["discovered_devices"].extend(devices)
        
        print(f"\n{'=' * 50}")
        print(f"Scan complete: {len(results['discovered_devices'])} devices found")
        
        # Count MES devices
        mes_count = sum(1 for d in results["discovered_devices"] if d["mes_ports"])
        print(f"MES devices: {mes_count}")
        
        return results


def main():
    parser = ArgumentParser(description="MES Network Scanner")
    parser.add_argument("--output", "-o", default="network_scan.json", help="Output JSON file")
    parser.add_argument("--timeout", "-t", type=float, default=2.0, help="Timeout per port (seconds)")
    parser.add_argument("--scan-timeout", "-st", type=int, default=120, help="Max scan time per subnet (seconds)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    scanner = NetworkScanner(timeout=args.timeout, scan_timeout=args.scan_timeout)
    results = scanner.run_full_scan()
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
