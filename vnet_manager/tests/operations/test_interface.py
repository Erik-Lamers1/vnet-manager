from unittest.mock import Mock, MagicMock, ANY, call

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.interface import (
    get_vnet_interface_names_from_config,
    get_machines_by_vnet_interface_name,
    show_vnet_interface_status,
    show_vnet_veth_interface_status,
    check_if_interface_exists,
    create_vnet_interface,
    create_veth_interface,
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


class TestShowVNetVethInterfaceStatus(VNetTestCase):
    def setUp(self) -> None:
        self.iproute_obj = Mock()
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute.return_value = self.iproute_obj
        self.iproute_obj.link.return_value = [
            {
                "state": "up",
                "attrs": [
                    ("IFLA_ADDRESS", "mac"),
                    ("IFLA_LINK", "dev2"),
                    ("IFLA_IFNAME", "peer"),
                    ("IFLA_MASTER", "eth0"),
                    ("IFLA_IFNAME", "master"),
                ],
            }
        ]
        self.iproute_obj.link_lookup.return_value = ["dev1"]
        self.tabulate = self.set_up_patch("vnet_manager.operations.interface.tabulate")

    def test_show_vnet_veth_interface_status_calls_iproute(self):
        show_vnet_veth_interface_status(settings.CONFIG)
        self.iproute.assert_called_once_with()

    def test_show_vnet_veth_interface_status_calls_ip_lookup(self):
        calls = [call(ifname=i) for i in settings.CONFIG["veths"]]
        show_vnet_veth_interface_status(settings.CONFIG)
        self.iproute_obj.link_lookup.assert_has_calls(calls)

    def test_show_vnet_veth_interface_status_calls_ip_link(self):
        show_vnet_veth_interface_status(settings.CONFIG)
        calls = [call("get", index="dev1"), call("get", index="dev2"), call("get", index="eth0")]
        self.iproute_obj.link.assert_has_calls(calls)

    def test_show_vnet_veth_interface_status_calls_tabulate(self):
        show_vnet_veth_interface_status(settings.CONFIG)
        self.tabulate.assert_called_once_with(
            [["vnet-veth1", "up", "mac", "peer", "peer"], ["vnet-veth0", "up", "mac", "peer", "peer"]],
            headers=["Name", "Status", "L2_addr", "Peer", "Master"],
            tablefmt="pretty",
        )

    def test_show_vnet_veth_interface_status_calls_tabulate_when_dev_does_not_exist(self):
        self.iproute_obj.link_lookup.return_value = []
        show_vnet_veth_interface_status(settings.CONFIG)
        self.tabulate.assert_called_once_with(
            [["vnet-veth1", "NA", "NA", "NA", "vnet-br1"], ["vnet-veth0", "NA", "NA", "NA", "vnet-br0"]],
            headers=["Name", "Status", "L2_addr", "Peer", "Master"],
            tablefmt="pretty",
        )


class TestCheckIfInterfaceExists(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute.return_value.link_lookup.return_value = [1]

    def test_check_if_interface_exists_calls_iproute_lookup(self):
        check_if_interface_exists("dev1")
        self.iproute.return_value.link_lookup.assert_called_once_with(ifname="dev1")

    def test_check_if_interface_exists_returns_true_if_it_exists(self):
        self.assertTrue(check_if_interface_exists("dev1"))

    def test_check_if_interface_exists_returns_false_if_it_does_not_exist(self):
        self.iproute.return_value.link_lookup.return_value = []
        self.assertFalse(check_if_interface_exists("dev1"))


class TestCreateVNetInterface(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.configure_int = self.set_up_patch("vnet_manager.operations.interface.configure_vnet_interface")

    def test_create_vnet_interface_calls_iproute_link_add(self):
        create_vnet_interface("dev1")
        self.iproute.return_value.link.assert_called_once_with("add", ifname="dev1", kind="bridge")

    def test_create_vnet_interface_calls_configure_vnet_interface(self):
        create_vnet_interface("dev1")
        self.configure_int.assert_called_once_with("dev1")


class TestCreateVethInterface(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")

    def test_create_veth_interface_calls_iproute_link_add(self):
        create_veth_interface("vnet-veth0", settings.CONFIG["veths"]["vnet-veth0"])
        self.iproute.return_value.link.assert_called_once_with("add", ifname="vnet-veth0", kind="veth", peer="vnet-veth1")

    def test_create_veth_interface_does_nothing_when_called_with_interface_without_a_peer(self):
        create_veth_interface("vneth-veth0", settings.CONFIG["veths"]["vnet-veth1"])
        self.assertFalse(self.iproute.return_value.link.called)
