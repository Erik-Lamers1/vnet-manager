from unittest.mock import Mock, MagicMock, ANY

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.interface import (
    get_vnet_interface_names_from_config,
    get_machines_by_vnet_interface_name,
    show_vnet_interface_status,
)
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


class TestShowVNetInterfaceStatus(VNetTestCase):
    def setUp(self) -> None:
        self.iproute_obj = Mock()
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute.return_value = self.iproute_obj
        self.iproute_obj.link_lookup.return_value = "dev1"
        self.ndb_obj = MagicMock()
        self.ndb = self.set_up_patch("vnet_manager.operations.interface.NDB", themock=MagicMock())
        self.check_if_sniffer_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_sniffer_exists")
        self.check_if_sniffer_exists.return_value = True
        self.tabulate = self.set_up_patch("vnet_manager.operations.interface.tabulate")
        self.interfaces = self.set_up_patch("vnet_manager.operations.interface.get_vnet_interface_names_from_config")
        self.interfaces.return_value = ["vnet-br0"]

    def test_show_vnet_interface_status_calls_iproute(self):
        show_vnet_interface_status(settings.CONFIG)
        self.iproute.assert_called_once_with()

    def test_show_vnet_interface_status_calls_ndb(self):
        show_vnet_interface_status(settings.CONFIG)
        self.ndb.assert_called_once_with(log="off")

    def test_show_vnet_interfaces_status_calls_get_vnet_interface_names_from_config(self):
        show_vnet_interface_status(settings.CONFIG)
        self.interfaces.assert_called_once_with(settings.CONFIG)

    def test_show_vnet_interface_status_calls_get_machines_by_vnet_interface_name(self):
        machines = self.set_up_patch("vnet_manager.operations.interface.get_machines_by_vnet_interface_name")
        machines.return_value = []
        show_vnet_interface_status(settings.CONFIG)
        machines.assert_called_once_with(settings.CONFIG, self.interfaces.return_value[0])

    def test_show_vnet_interface_status_calls_link_lookup(self):
        show_vnet_interface_status(settings.CONFIG)
        self.iproute_obj.link_lookup.assert_called_once_with(ifname=self.interfaces.return_value[0])

    def test_show_vnet_interface_status_calls_check_if_sniffer_exists(self):
        show_vnet_interface_status(settings.CONFIG)
        self.check_if_sniffer_exists.assert_called_once_with(self.interfaces.return_value[0])

    def test_show_vnet_interface_status_calls_tabulate(self):
        show_vnet_interface_status(settings.CONFIG)
        self.tabulate.assert_called_once_with(
            [["vnet-br0", ANY, ANY, self.check_if_sniffer_exists.return_value, True, "router100, router101"]],
            headers=["Name", "Status", "L2_addr", "Sniffer", "STP", "Used by"],
            tablefmt="pretty",
        )

    def test_show_vnet_interface_status_makes_correct_output_if_interface_does_not_exist(self):
        self.iproute_obj.link_lookup.return_value = []
        show_vnet_interface_status(settings.CONFIG)
        self.assertFalse(self.check_if_sniffer_exists.called)
        self.tabulate.assert_called_once_with(
            [["vnet-br0", "NA", "NA", "NA", "NA", "router100, router101"]],
            headers=["Name", "Status", "L2_addr", "Sniffer", "STP", "Used by"],
            tablefmt="pretty",
        )

    def test_show_vnet_interface_status_displays_result_if_check_if_sniffer_exists(self):
        self.check_if_sniffer_exists.return_value = False
        show_vnet_interface_status(settings.CONFIG)
        self.tabulate.assert_called_once_with(
            [["vnet-br0", ANY, ANY, self.check_if_sniffer_exists.return_value, True, "router100, router101"]],
            headers=["Name", "Status", "L2_addr", "Sniffer", "STP", "Used by"],
            tablefmt="pretty",
        )
