from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.interface import get_vnet_interface_names_from_config, get_machines_by_vnet_interface_name
from vnet_manager.conf import settings


class TestGetVNetInterfaceNamesFromConfig(VNetTestCase):
    def test_get_vnet_interface_names_from_config_returns_a_list(self):
        self.assertIsInstance(get_vnet_interface_names_from_config(settings.CONFIG), list)

    def test_get_vnet_interface_names_from_config_is_equal_to_the_length_of_defined_switches(self):
        self.assertEqual(len(get_vnet_interface_names_from_config(settings.CONFIG)), settings.CONFIG["switches"])

    def test_get_vnet_interface_names_from_config_startswith_vnet_bridge_name(self):
        for interface in get_vnet_interface_names_from_config(settings.CONFIG):
            self.assertRegex(interface, r"^{}".format(settings.VNET_BRIDGE_NAME))


class TestGetMachinesByVNetInterfaceName(VNetTestCase):
    def test_get_machines_by_vnet_interface_name_returns_a_list(self):
        self.assertIsInstance(get_vnet_interface_names_from_config(settings.CONFIG), list)

    def test_get_machines_by_vnet_interface_name_returns_the_correct_machines_per_interface(self):
        interface_mapping = {
            settings.VNET_BRIDGE_NAME + "0": ["router100", "router101"],
            settings.VNET_BRIDGE_NAME + "1": ["router101", "router102"],
        }
        for interface in interface_mapping:
            self.assertEqual(get_machines_by_vnet_interface_name(settings.CONFIG, interface), interface_mapping[interface])
