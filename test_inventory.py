#!/usr/bin/env python3

import unittest
from unittest.mock import patch, MagicMock
import inventory


class TestLocalNetworkInventory(unittest.TestCase):

    @classmethod
    @patch("inventory.nmap")
    @patch("inventory.netifaces")
    def setUpClass(cls, mock_netifaces, mock_nmap):

        ip = '192.168.0.1'
        interfaces = ['lo', 'eth0', 'wlo1', 'docker0']

        mock_netifaces.AF_INET = 2
        mock_netifaces.interfaces.return_value = interfaces
        mock_netifaces.ifaddresses.return_value = \
            {2: [{'addr': ip,
                  'netmask': '255.255.255.0'}]}

        port_scanner = MagicMock()
        mock_nmap.PortScanner.return_value = port_scanner
        port_scanner.all_hosts.return_value = [ip]
        mock_host = MagicMock()
        mock_host.has_tcp.return_value = True
        mock_host.__getitem__.return_value = {22: {"state": "open"}}
        port_scanner.__getitem__.return_value = mock_host

        cls.inventory = inventory.LocalNetworkInventory()
        cls.scanner = port_scanner
        cls.netifaces = mock_netifaces

    def test_one_scan(self):
        self.netifaces.interfaces.assert_called_once()
        self.scanner.scan.assert_called_once()

    def test_discover_cidr(self):
        self.netifaces.interfaces.assert_called_once()
        assert self.inventory.cidrs[0] == "192.168.0.0/24", \
            f"Found {self.inventory.cidrs}"

    def test_discover_host(self):
        assert "192.168.0.1" in self.inventory.ssh_hosts,\
            f"Did not find in {self.inventory.ssh_hosts}"


if __name__ == "__main__":
    unittest.main()
