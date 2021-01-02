from re import match, IGNORECASE

from vnet_manager.utils.mac import random_mac_generator
from vnet_manager.tests import VNetTestCase

VALID_MAC = r"^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$"


class TestRandomMACGenerator(VNetTestCase):
    def test_random_mac_generator_returns_string(self):
        self.assertIsInstance(random_mac_generator(), str)

    def test_random_mac_generator_starts_with(self):
        self.assertTrue(random_mac_generator().startswith("02:00"))

    def test_random_mac_generator_generate_valid_mac_address(self):
        self.assertTrue(match(VALID_MAC, random_mac_generator(), IGNORECASE))
