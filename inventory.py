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

import os
import sys
import argparse
import nmap

try:
    import json
except ImportError:
    import simplejson as json

class LocalNetworkInventory(object):

    def __init__(self):
        self.inventory = {}
        self._read_cli_args()

        # Called with `--cidr [IPv4_CIDR1[,IPv4_CIDR2...]]`.
        if self.args.cidr:
            self._cidr_string = self.args.cidr

        self._discover_inventory()

        print(json.dumps(self.inventory))

    def _discover_inventory(self.):

    # Example inventory for testing.
    def example_inventory(self):
        return {
            'group': {
                'hosts': ['192.168.28.71', '192.168.28.72'],
                'vars': {
                    'ansible_ssh_user': 'vagrant',
                    'ansible_ssh_private_key_file':
                        '~/.vagrant.d/insecure_private_key',
                    'ansible_python_interpreter':
                        '/usr/bin/python3',
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
        parser.add_argument('--cidr', action = 'store_true')
        self.args = parser.parse_args()

# Get the inventory.
ExampleInventory()

