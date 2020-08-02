from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.interface import get_vnet_interface_names_from_config
from vnet_manager.conf import settings


class TestGetVNetInterfaceNamesFromConfig(VNetTestCase):
    def test_get_vnet_interface_names_from_config_is_equal_to_the_length_of_defined_switches(self):
        self.assertEqual(len(get_vnet_interface_names_from_config(settings.CONFIG)), settings.CONFIG["switches"])

    def test_get_vnet_interface_names_from_config_startswith_vnet_bridge_name(self):
        for interface in get_vnet_interface_names_from_config(settings.CONFIG):
            self.assertRegex(interface, r"^{}".format(settings.VNET_BRIDGE_NAME))
