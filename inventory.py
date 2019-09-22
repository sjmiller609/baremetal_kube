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

import argparse
import netifaces
import ipaddress

try:
    import json
except ImportError:
    import simplejson as json


class LocalNetworkInventory(object):

    def __init__(self):
        self.inventory = {}
        self._read_cli_args()

        self._discover_inventory()

        print(json.dumps(self.inventory))

    def _discover_inventory(self):
        pass

    def _discover_cidr(self):
        self.cidr = ""
        interfaces = netifaces.interfaces()
        interfaces = list(filter(lambda x: x[0] == "e", interfaces))
        if len(interfaces) < 1:
            raise Exception("Did not detect any interfaces starting with "
                            "the character 'e'")
        for interface in interfaces:
            print(f"Detected interface {interface}:")
            for address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                ip_address = address['addr']
                netmask = address['netmask']
                if not ipaddress.ip_address(ip_address).version == 4:
                    print(f"Ignoring non-IPv4 address: {ip_address}")
                    continue
                remove_host_bits = ip_address.split(".")
                remove_host_bits.pop()
                remove_host_bits.append("0")
                remove_host_bits = ".".join(remove_host_bits)
                netmask = ipaddress.IPv4Network(
                    f"{remove_host_bits}/{netmask}").prefixlen
                self.cidr += f"{remove_host_bits}/{netmask},"
        self.cidr = self.cidr[:-1]

    def example_inventory(self):
        return {
            'group': {
                'hosts': ['192.168.28.71', '192.168.28.72'],
                'vars': {
                    'ansible_ssh_user': 'vagrant',
                    'ansible_ssh_private_key_file':
                    '~/.vagrant.d/insecure_private_key',
                    'ansible_python_interpreter': '/usr/bin/python3',
                    'example_variable': 'value'
                }
            },
            '_meta': {
                'hostvars': {
                    '192.168.28.71': {
                        'host_specific_var': 'foo'
                    },
                    '192.168.28.72': {
                        'host_specific_var': 'bar'
                    }
                }
            }
        }

    # Read the command line args passed to the script.
    def _read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--cidr', action='store_true')
        self.args = parser.parse_args()


# Get the inventory.
LocalNetworkInventory()
