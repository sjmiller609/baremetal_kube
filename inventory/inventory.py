#!/usr/bin/env python3

'''
Local network any SSH

If any hosts are present on a local network attached to a wired interface,
and we can connect using either a username/password or a username/SSH key
then add them to the inventory, grouped by type.

types:
  container_linux
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

        self.hostvars = \
            {
                'localhost': {
                    'ansible_connection': 'local',
                    'ansible_python_interpreter': '/usr/bin/python',
                    'ansible_become': 'yes',
                    'bin_dir': '/opt/bin'
                }
            }

        self._discover_inventory()
        print(json.dumps(self.inventory))

    def _discover_inventory(self):
        self._discover_cidr()
        self._discover_ssh_open()
        self._discover_ssh_connect()
        self._build_inventory()
        # self._sort_invetory()

    def _get_mac_from_ip(host):
        return hash(str(self.nm[host]))

    def _sort_inventory(self):
        for key in self.inventory:
            if self.inventory[key].get('hosts'):
                self.inventoy[key]['hosts'].sort(
                    key=lambda host: self._get_mac_from_ip(host))


    def _get_motd(self, host, **kwargs):
        motd = ''
        cpu_mhz = 0
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, **kwargs)
            stdin, stdout, stderr = client.exec_command('cat /etc/motd')
            motd = stdout.read().decode('utf-8')
            stdin, stdout, stderr = client.exec_command("lscpu | grep -i 'max mhz' | awk '{ print $4 }'")
            cpu_mhz = float(stdout.read().decode('utf-8'))
        except Exception as e:
            sys.stderr.write(f'{e}\n')
        finally:
            client.close()
            return motd, cpu_mhz

    def _detect_os(self, host):
        motd, cpu_mhz = self._get_motd(host,
                              port=22,
                              username='core')
        if 'container linux' in motd.lower():
            return 'container_linux', cpu_mhz
        motd, cpu_mhz = self._get_motd(host,
                              port=22,
                              username='pi')
        if 'raspberrypi' in motd.lower():
            return 'raspberry_pi', cpu_mhz
        motd, cpu_mhz = self._get_motd(host,
                              port=22,
                              username=self.USERNAME,
                              password=self.PASSWORD)
        if 'edgeos' in motd.lower():
            return 'edgeos', cpu_mhz

        return None, cpu_mhz

    def _discover_ssh_connect(self):

        self.routers = []
        self.container_linux = []
        self.raspberry_pi = []

        for host in self.ssh_hosts:
            os, cpu_mhz = self._detect_os(host)
            if os == 'edgeos':
                sys.stderr.write(f'Detected EdgeOS on host: {host}\n')
                self.routers.append(host)
            elif os == 'container_linux':
                sys.stderr.write(f'Detected Container Linux on host: {host}\n')
                hostname = f'node{len(self.container_linux)}'
                self.container_linux.append((hostname, cpu_mhz))
                self.hostvars[hostname] = {
                    'ansible_host': host,
                    'ansible_user': 'core',
                    'ansible_ssh_private_key_file': '~/.ssh/id_rsa',
                    'ansible_python_interpreter': '/opt/bin/python',
                    'bin_dir': '/opt/bin',
                    'ansible_become': 'yes'
                }
            elif os == 'raspberry_pi':
                sys.stderr.write(f'Detected Raspberry Pi on host: {host}\n')
                hostname = f'pi{len(self.raspberry_pi)}'
                self.raspberry_pi.append((hostname, cpu_mhz))
                self.hostvars[hostname] = {
                    'ansible_host': host,
                    'ansible_user': 'pi',
                    'ansible_ssh_private_key_file': '~/.ssh/id_rsa'
                }

            else:
                sys.stderr.write(f'Did not detect Container Linux, EdgeOS, or Raspbian on host: {host}\n')

        if len(self.routers) > 1:
            raise Exception(
                'Currently, only a 1 router configuration is supported. '
                f'Found {self.routers}')

    def _discover_ssh_open(self):

        for cidr in self.cidrs:
            sys.stderr.write(f'Scanning port 22 in network {cidr}\n')
            self.nm.scan(hosts=cidr, ports='22', arguments='-n -Pn')

        self.ssh_hosts = []

        for host in self.nm.all_hosts():
            if self.nm[host].has_tcp(22) and \
               self.nm[host]['tcp'][22]['state'] == 'open':
                self.ssh_hosts.append(host)

    def _discover_cidr(self):
        self.cidrs = []
        interfaces = netifaces.interfaces()
        interfaces = list(filter(lambda x: x[0] == 'e', interfaces))

        if len(interfaces) < 1:
            raise Exception('Did not detect any interfaces starting '
                            "with the character 'e'")

        for interface in interfaces:
            sys.stderr.write(f'Detected interface {interface}:\n')

            if not netifaces.AF_INET in netifaces.ifaddresses(interface):
                sys.stderr.write(f'Interface {interface} does not have a configured IP address. Configuring to the default network for EdgeLITE router:\n')
                check_output(['ifconfig', interface, '192.168.1.100'])
                check_output(['ifconfig', interface, 'netmask', '255.255.255.0'])

            for address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                ip_address = address['addr']
                netmask = address['netmask']

                if not ipaddress.ip_address(ip_address).version == 4:
                    sys.stderr.write(
                        f'Ignoring non-IPv4 address: {ip_address}\n')

                    continue
                remove_host_bits = ip_address.split('.')
                remove_host_bits.pop()
                remove_host_bits.append('0')
                remove_host_bits = '.'.join(remove_host_bits)
                netmask = ipaddress.IPv4Network(
                    f'{remove_host_bits}/{netmask}').prefixlen
                cidr = f'{remove_host_bits}/{netmask}'
                sys.stderr.write(f'Detected cidr {cidr}\n')
                self.cidrs.append(cidr)

    def _build_inventory(self):
        # Sort hosts by CPU MHz
        self.container_linux.sort(key = lambda x: x[1], reverse=True)
        self.container_linux = [pair[0] for pair in self.container_linux]
        self.raspberry_pi.sort(key = lambda x: x[1], reverse=True)
        self.raspberry_pi = [pair[0] for pair in self.container_linux]

        self.inventory = {
            'all': {
                'children': ['routers', 'container_linux', 'pxe_servers','k8s-cluster', 'raspberry_pi']
            },
            'routers': {
                'hosts': self.routers,
                'vars': {
                    'ansible_user': self.USERNAME,
                    'ansible_password': self.PASSWORD,
                    'ansible_connection': 'network_cli',
                    'ansible_network_os': 'edgeos'
                }
            },
            'pxe_server': {
                'hosts': ['localhost'],
            },
            'container_linux': {
                'hosts': self.container_linux,
            },
            'etcd': {
            },
            'kube-node': {
            },
            'kube-master': {
            },
            'k8s-cluster': {
                'children': ['k3s-server','k3s-agent']
            },
            '_meta': {
                'hostvars': self.hostvars
            }
        }
        self.inventory['kube-node']['hosts'] = \
            self.container_linux
        self.inventory['kube-master']['hosts'] = \
            self.container_linux[:3]
        num_hosts = len(self.container_linux)

        if not num_hosts % 2 and num_hosts < 7:
            self.inventory['etcd']['hosts'] = \
                self.container_linux[1:7]
        else:
            self.inventory['etcd']['hosts'] = \
                self.container_linux[:7]

if __name__ == '__main__':
    # Get the inventory.
    LocalNetworkInventory()
