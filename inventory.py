#!/usr/bin/env python3
'''
Local network any SSH

If any hosts are present on a local network attached to a wired interface,
and we can connect using either a username/password or a username/SSH key
then add them to the inventory, grouped by type.

types:
  kube_nodes
  edgeos_router

Custom dynamic inventory script for Ansible, in Python.
'''

import sys
import netifaces
import ipaddress
import paramiko
import nmap
from subprocess import check_output

try:
    import json
except ImportError:
    import simplejson as json


class LocalNetworkInventory(object):

    USERNAME = 'ubnt'
    PASSWORD = 'ubnt'

    def __init__(self):
        self.inventory = {}
        self.nm = nmap.PortScanner()

        self._discover_inventory()

        print(json.dumps(self.inventory))

    def _discover_inventory(self):
        self._discover_cidr()
        self._discover_ssh_open()
        self._discover_ssh_connect()
        self._build_inventory()

    def _discover_ssh_connect(self):

        self.routers = []
        self.nodes = []

        for host in self.ssh_hosts:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host,
                               port=22,
                               username=self.USERNAME,
                               password=self.PASSWORD)
                stdin, stdout, stderr = client.exec_command('cat /etc/motd')
                motd = stdout.read().decode('utf-8')

                if "edgeos" in motd.lower():
                    sys.stderr.write(f"Detected EdgeOS on host: {host}\n")
                    self.routers.append(host)
                else:
                    sys.stderr.write(motd)

            except Exception:
                pass
            finally:
                client.close()

        if len(self.routers) > 1:
            raise Exception(
                "Currently, only a 1 router configuration is supported. "
                f"Found {self.routers}")

    def _discover_ssh_open(self):

        for cidr in self.cidrs:
            sys.stderr.write(f"Scanning port 22 in network {cidr}\n")
            self.nm.scan(hosts=cidr, ports='22', arguments='-n', sudo=False)

        self.ssh_hosts = []

        for host in self.nm.all_hosts():
            if self.nm[host].has_tcp(22) and \
               self.nm[host]['tcp'][22]['state'] == 'open':
                self.ssh_hosts.append(host)

    def _discover_cidr(self):
        self.cidrs = []
        interfaces = netifaces.interfaces()
        interfaces = list(filter(lambda x: x[0] == "e", interfaces))

        if len(interfaces) < 1:
            raise Exception("Did not detect any interfaces starting "
                            "with the character 'e'")

        for interface in interfaces:
            sys.stderr.write(f"Detected interface {interface}:\n")

            if not netifaces.AF_INET in netifaces.ifaddresses(interface):
                sys.stderr.write(f"Interface {interface} does not have a configured IP address. Configuring to the default network for EdgeLITE router:\n")
                check_output(["ifconfig", interface, "192.168.1.100"])
                check_output(["ifconfig", interface, "netmask", "255.255.255.0"])

            for address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                ip_address = address['addr']
                netmask = address['netmask']

                if not ipaddress.ip_address(ip_address).version == 4:
                    sys.stderr.write(
                        f"Ignoring non-IPv4 address: {ip_address}\n")

                    continue
                remove_host_bits = ip_address.split(".")
                remove_host_bits.pop()
                remove_host_bits.append("0")
                remove_host_bits = ".".join(remove_host_bits)
                netmask = ipaddress.IPv4Network(
                    f"{remove_host_bits}/{netmask}").prefixlen
                cidr = f"{remove_host_bits}/{netmask}"
                sys.stderr.write(f"Detected cidr {cidr}\n")
                self.cidrs.append(cidr)

    def _build_inventory(self):
        self.inventory = {
            'all': {
                'children': ['routers', 'kube_nodes', 'pxe_servers']
            },
            "routers": {
                "hosts": self.routers,
                "vars": {
                    "ansible_user": self.USERNAME,
                    "ansible_password": self.PASSWORD,
                    "ansible_connection": "network_cli",
                    "ansible_network_os": "edgeos"
                }
            },
            "kube_nodes": {
                "hosts": self.routers
            },
            "pxe_server": {
                "hosts": ["localhost"],
            },
            "_meta": {
                "hostvars": {
                    "localhost": {
                        "ansible_connection": "local",
                        "ansible_python_interpreter": "/usr/bin/python"
                    }
                }
            }
        }


if __name__ == "__main__":
    # Get the inventory.
    LocalNetworkInventory()
