#!/usr/bin/env python3

import unittest
from unittest.mock import patch
from inventory import LocalNetworkInventory


class TestLocalNetworkInventory(unittest.TestCase):

    def test_instantiation(self):
        LocalNetworkInventory()

    @patch("inventory.nmap")
    def test_discover_cidr(self, mock_nmap):
        generator = LocalNetworkInventory()
        generator._discover_cidr()
        assert generator.cidr == "192.168.1.0/24", \
            f"Found {generator.cidr}"


if __name__ == "__main__":
    unittest.main()
