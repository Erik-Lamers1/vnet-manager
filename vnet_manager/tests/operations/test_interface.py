import shlex
from os.path import join
from subprocess import DEVNULL, CalledProcessError
from unittest.mock import Mock, MagicMock, ANY, call
from copy import deepcopy

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.interface import (
    get_vnet_interface_names_from_config,
    get_machines_by_vnet_interface_name,
    show_vnet_interface_status,
    show_vnet_veth_interface_status,
    check_if_interface_exists,
    create_vnet_interface,
    create_veth_interface,
    create_vnet_interface_iptables_rules,
    configure_vnet_interface,
    configure_veth_interface,
    bring_up_vnet_interfaces,
    ensure_vnet_veth_interfaces,
    check_if_sniffer_exists,
    bring_down_vnet_interfaces,
    delete_vnet_interfaces,
    start_tcpdump_on_vnet_interface,
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
            settings.VNET_BRIDGE_NAME + "1": ["router101", "host102"],
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
        self.ndb.assert_called_once_with(log=False)

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


class TestCreateVNetInterfaceIPtablesDropRules(VNetTestCase):
    def setUp(self) -> None:
        self.check_call = self.set_up_patch("vnet_manager.operations.interface.check_call")
        self.check_call.side_effect = [CalledProcessError(1, "test"), 0]
        self.logger = self.set_up_patch("vnet_manager.operations.interface.logger")

    def test_create_vnet_interface_iptables_drop_rules_makes_correct_check_call_calls(self):
        calls = [
            call(shlex.split("iptables -C OUTPUT -o dev1 -j DROP"), stderr=DEVNULL),
            call(shlex.split("iptables -A OUTPUT -o dev1 -j DROP")),
        ]
        create_vnet_interface_iptables_rules("dev1")
        self.check_call.assert_has_calls(calls)
        self.logger.info.assert_called_once_with("Creating IPtables DROP rule to the outside world for VNet interface dev1")

    def test_create_vnet_interface_iptables_drop_rules_does_not_add_rules_if_they_already_exist(self):
        self.check_call.side_effect = [0, 0]
        create_vnet_interface_iptables_rules("dev1")
        self.check_call.assert_called_once_with(shlex.split("iptables -C OUTPUT -o dev1 -j DROP"), stderr=DEVNULL)
        self.logger.debug.assert_called_once_with("IPtables DROP rule for VNet interface dev1 already exists, skipping creation")

    def test_create_vnet_interface_iptables_drop_rules_logs_error_if_both_commands_fail(self):
        self.check_call.side_effect = [CalledProcessError(1, "test"), CalledProcessError(1, "test")]
        create_vnet_interface_iptables_rules("dev1")
        self.logger.error.assert_called_once_with("Unable to create IPtables rule, got output: None")


class TestConfigureVNetInterface(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute_obj = Mock()
        self.iproute.return_value = self.iproute_obj
        self.iproute_obj.link_lookup.return_value = [1]
        self.rand_mac = self.set_up_patch("vnet_manager.operations.interface.random_mac_generator")

    def test_configure_vnet_interfaces_calls_ip_route(self):
        configure_vnet_interface("test")
        self.iproute.assert_called_once_with()

    def test_configure_vnet_interface_looks_up_passed_interface(self):
        configure_vnet_interface("test")
        self.iproute_obj.link_lookup.assert_called_once_with(ifname="test")

    def test_configure_vnet_interface_calls_random_mac_generator(self):
        configure_vnet_interface("test")
        self.rand_mac.assert_called_once_with()

    def test_configure_vnet_interface_makes_correct_ip_set_calls(self):
        calls = [
            call("set", index=1, state="down"),
            call("set", index=1, address=self.rand_mac.return_value),
            call("set", index=1, state="up"),
        ]
        configure_vnet_interface("test")
        self.iproute_obj.link.assert_has_calls(calls)


class TestConfigureVethInterface(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute_obj = Mock()
        self.iproute.return_value = self.iproute_obj
        self.iproute_obj.link_lookup.side_effect = [[1], [2]]
        self.data = settings.CONFIG["veths"]["vnet-veth1"]

    def test_configure_veth_interface_calls_ip_route(self):
        configure_veth_interface("test", self.data)
        self.iproute.assert_called_once_with()

    def test_configure_veth_interface_makes_correct_ip_lookup_calls(self):
        calls = [call(ifname="test"), call(ifname=settings.CONFIG["veths"]["vnet-veth1"]["bridge"])]
        configure_veth_interface("test", self.data)
        self.iproute_obj.link_lookup.assert_has_calls(calls)

    def test_configure_veth_interface_calls_ip_link(self):
        configure_veth_interface("test", self.data)
        self.iproute_obj.link.assert_called_once_with("set", index=1, master=2)


class TestBringUpVNetInterfaces(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute_obj = Mock()
        self.iproute.return_value = self.iproute_obj
        self.get_vnet_interface_names = self.set_up_patch("vnet_manager.operations.interface.get_vnet_interface_names_from_config")
        self.get_vnet_interface_names.return_value = ["int1", "int2"]
        self.check_if_interface_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_interface_exists")
        self.check_if_interface_exists.return_value = False
        self.create_vnet_interface = self.set_up_patch("vnet_manager.operations.interface.create_vnet_interface")
        self.create_vnet_interface_block_rules = self.set_up_patch("vnet_manager.operations.interface.create_vnet_interface_iptables_rules")
        self.check_if_sniffer_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_sniffer_exists")
        self.check_if_sniffer_exists.return_value = False
        self.start_tcpdump_on_interface = self.set_up_patch("vnet_manager.operations.interface.start_tcpdump_on_vnet_interface")
        self.ensure_vnet_veth_interfaces = self.set_up_patch("vnet_manager.operations.interface.ensure_vnet_veth_interfaces")
        self.config = deepcopy(settings.CONFIG)
        self.expected_vnet_interface_calls = [call(i) for i in self.get_vnet_interface_names.return_value]

    def test_bring_up_vnet_interfaces_calls_ip_route(self):
        bring_up_vnet_interfaces(self.config)
        self.iproute.assert_called_once_with()

    def test_bring_up_vnet_interfaces_calls_get_vnet_interface_names_from_config(self):
        bring_up_vnet_interfaces(self.config)
        self.get_vnet_interface_names.assert_called_once_with(self.config)

    def test_bring_up_vnet_interfaces_calls_check_if_interface_exists_with_interface_names(self):
        bring_up_vnet_interfaces(self.config)
        self.check_if_interface_exists.assert_has_calls(self.expected_vnet_interface_calls)

    def test_bring_up_vnet_interfaces_calls_create_vnet_interface_with_interface_names(self):
        bring_up_vnet_interfaces(self.config)
        self.create_vnet_interface.assert_has_calls(self.expected_vnet_interface_calls)

    def test_bring_up_vnet_interfaces_does_not_call_create_interface_if_the_interface_already_exists(self):
        self.check_if_interface_exists.return_value = True
        bring_up_vnet_interfaces(self.config)
        self.assertFalse(self.create_vnet_interface.called)

    def test_bring_up_vnet_interfaces_calls_create_vnet_interface_iptables_rules(self):
        bring_up_vnet_interfaces(self.config)
        self.create_vnet_interface_block_rules.assert_has_calls(self.expected_vnet_interface_calls)

    def test_bring_up_vnet_interfaces_calls_ip_link_to_bring_up_interfaces(self):
        calls = [call("set", ifname=i, state="up") for i in self.get_vnet_interface_names.return_value]
        bring_up_vnet_interfaces(self.config)
        self.iproute_obj.link.assert_has_calls(calls)

    def test_bring_up_vnet_interfaces_does_not_create_sniffer_by_default(self):
        bring_up_vnet_interfaces(self.config)
        self.assertFalse(self.start_tcpdump_on_interface.called)

    def test_bring_up_vnet_interfaces_calls_sniffer_when_sniffer_argument_passed(self):
        bring_up_vnet_interfaces(self.config, sniffer=True)
        self.start_tcpdump_on_interface.assert_has_calls(self.expected_vnet_interface_calls)

    def test_bring_up_vnet_interfaces_calls_check_if_sniffer_exists(self):
        bring_up_vnet_interfaces(self.config, sniffer=True)
        self.check_if_sniffer_exists.assert_has_calls(self.expected_vnet_interface_calls)

    def test_bring_up_vnet_interfaces_does_not_call_start_sniffer_when_the_sniffer_already_exists(self):
        self.check_if_sniffer_exists.return_value = True
        bring_up_vnet_interfaces(self.config, sniffer=True)
        self.assertFalse(self.start_tcpdump_on_interface.called)

    def test_bring_up_vnet_interfaces_calls_ensure_vnet_veth_interfaces(self):
        bring_up_vnet_interfaces(self.config)
        self.ensure_vnet_veth_interfaces.assert_called_once_with(self.config)

    def test_bring_up_vnet_interfaces_does_not_calls_ensure_vnet_veth_interface_if_no_veth_interfaces_present_in_config(self):
        del self.config["veths"]
        bring_up_vnet_interfaces(self.config)
        self.assertFalse(self.ensure_vnet_veth_interfaces.called)


class TestEnsureVNetVethInterfaces(VNetTestCase):
    def setUp(self) -> None:
        self.config = deepcopy(settings.CONFIG)
        self.ndb = self.set_up_patch("vnet_manager.operations.interface.NDB", themock=MagicMock())
        self.check_if_interface_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_interface_exists")
        self.check_if_interface_exists.return_value = False
        self.create_veth_interface = self.set_up_patch("vnet_manager.operations.interface.create_veth_interface")
        self.configure_veth_interface = self.set_up_patch("vnet_manager.operations.interface.configure_veth_interface")
        self.configure_vnet_interface = self.set_up_patch("vnet_manager.operations.interface.configure_vnet_interface")

    def test_ensure_vnet_veth_interfaces_calls_ndb(self):
        ensure_vnet_veth_interfaces(self.config)
        self.ndb.assert_called_with(log=False)

    def test_ensure_vnet_veth_interfaces_set_stp_state_to_correct_state_according_to_config(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call("vnet-br1"), call("vnet-br0")]
        self.assertIn(calls, self.ndb.return_value.interfaces.__getitem__.call_args_list)

    def test_ensure_vnet_veth_interfaces_does_not_call_ndb_if_stp_not_in_int_data(self):
        del self.config["veths"]["vnet-veth1"]["stp"]
        ensure_vnet_veth_interfaces(self.config)
        self.assertNotIn(call("vnet-br1"), self.ndb.return_value.interfaces.__getitem__.call_args_list)

    def test_ensure_vnet_veth_interfaces_sets_correct_stp_state_on_bridge_ints(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call("br_stp_state", 1), call("br_stp_state", 0)]
        self.assertIn(calls, self.ndb.return_value.interfaces.__getitem__.return_value.__enter__.return_value.set.call_args_list)

    def test_ensure_vnet_veth_interfaces_checks_if_veth_interfaces_already_exist(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call(i) for i in self.config["veths"]]
        self.check_if_interface_exists.assert_has_calls(calls)

    def test_ensure_vnet_veth_interfaces_calls_create_veth_interfaces(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call(k, v) for k, v in self.config["veths"].items()]
        self.create_veth_interface.assert_has_calls(calls)

    def test_ensure_vnet_veth_interfaces_does_not_call_create_interfaces_if_they_already_exist(self):
        self.check_if_interface_exists.return_value = True
        self.assertFalse(self.create_veth_interface.called)

    def test_ensure_vnet_veth_interfaces_calls_configure_veth_interface(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call(k, v) for k, v in self.config["veths"].items()]
        self.configure_veth_interface.assert_has_calls(calls)

    def test_ensure_vnet_veth_interfaces_calls_configure_vnet_interface(self):
        ensure_vnet_veth_interfaces(self.config)
        calls = [call(i) for i in self.config["veths"]]
        self.configure_vnet_interface.assert_has_calls(calls)


class TestCheckIfSnifferExists(VNetTestCase):
    def setUp(self) -> None:
        self.process = Mock()
        self.process_iter = self.set_up_patch("vnet_manager.operations.interface.process_iter")
        self.process_iter.return_value = [self.process]
        self.process.cmdline.return_value = "testprocess testargs"

    def test_check_if_sniffer_exists_returns_false_if_sniffer_does_not_exist(self):
        self.assertFalse(check_if_sniffer_exists("dev0"))

    def test_check_if_sniffer_exists_returns_true_if_sniffer_exists(self):
        self.process.cmdline.return_value = "/usr/sbin/tcpdump -i dev1 -n"
        self.assertTrue(check_if_sniffer_exists("dev1"))


class TestBringDownVNetInterfaces(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute_obj = Mock()
        self.iproute.return_value = self.iproute_obj
        self.check_if_interface_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_interface_exists")
        self.config = deepcopy(settings.CONFIG)

    def test_bring_down_vnet_interfaces_calls_iproute(self):
        bring_down_vnet_interfaces(self.config)
        self.iproute.assert_called_once_with()

    def test_bring_down_vnet_interfaces_check_if_interface_exists_for_each_interface_in_config(self):
        calls = [call("vnet-veth1"), call("vnet-veth0"), call("vnet-br0"), call("vnet-br1")]
        bring_down_vnet_interfaces(self.config)
        self.check_if_interface_exists.assert_has_calls(calls)
        self.assertEqual(self.check_if_interface_exists.call_count, 4)

    def test_bring_down_vnet_interfaces_does_not_check_veth_interfaces_if_not_in_config(self):
        calls = [call("vnet-br0"), call("vnet-br1")]
        del self.config["veths"]
        bring_down_vnet_interfaces(self.config)
        self.check_if_interface_exists.assert_has_calls(calls)
        self.assertEqual(self.check_if_interface_exists.call_count, 2)

    def test_bring_down_vnet_interfaces_calls_ip_link_to_bring_down_interfaces(self):
        calls = [call("set", ifname=i, state="down") for i in ["vnet-veth1", "vnet-veth0", "vnet-br0", "vnet-br1"]]
        bring_down_vnet_interfaces(self.config)
        self.iproute_obj.link.assert_has_calls(calls)
        self.assertEqual(self.iproute_obj.link.call_count, 4)

    def test_bring_down_vnet_interfaces_down_not_bring_down_veth_interfaces_if_not_in_config(self):
        calls = [call("set", ifname=i, state="down") for i in ["vnet-br0", "vnet-br1"]]
        del self.config["veths"]
        bring_down_vnet_interfaces(self.config)
        self.iproute_obj.link.assert_has_calls(calls)
        self.assertEqual(self.iproute_obj.link.call_count, 2)

    def test_bring_down_vnet_interfaces_does_nothing_if_interfaces_do_not_exist(self):
        self.check_if_interface_exists.return_value = False
        bring_down_vnet_interfaces(self.config)
        self.assertFalse(self.iproute_obj.link.called)


class TestDeleteVNetInterfaces(VNetTestCase):
    def setUp(self) -> None:
        self.iproute = self.set_up_patch("vnet_manager.operations.interface.IPRoute")
        self.iproute_obj = Mock()
        self.iproute.return_value = self.iproute_obj
        self.check_if_interface_exists = self.set_up_patch("vnet_manager.operations.interface.check_if_interface_exists")
        self.config = deepcopy(settings.CONFIG)

    def test_delete_vnet_interfaces_calls_iproute(self):
        delete_vnet_interfaces(self.config)
        self.iproute.assert_called_once_with()

    def test_delete_vnet_interfaces_does_nothing_if_interfaces_do_not_exist(self):
        self.check_if_interface_exists.return_value = False
        delete_vnet_interfaces(self.config)
        self.assertFalse(self.iproute_obj.link.called)

    def test_delete_vnet_interfaces_check_if_interface_exists_for_each_interface_in_config(self):
        calls = [call("vnet-veth0"), call("vnet-br0"), call("vnet-br1")]
        delete_vnet_interfaces(self.config)
        self.check_if_interface_exists.assert_has_calls(calls)
        self.assertEqual(self.check_if_interface_exists.call_count, 3)

    def test_delete_vnet_interfaces_does_not_check_veth_interfaces_if_not_in_config(self):
        calls = [call("vnet-br0"), call("vnet-br1")]
        del self.config["veths"]
        delete_vnet_interfaces(self.config)
        self.check_if_interface_exists.assert_has_calls(calls)
        self.assertEqual(self.check_if_interface_exists.call_count, 2)

    def test_delete_vnet_interfaces_calls_ip_link_to_delete_interfaces(self):
        calls = [call("del", ifname=i) for i in ["vnet-veth0", "vnet-br0", "vnet-br1"]]
        delete_vnet_interfaces(self.config)
        self.iproute_obj.link.assert_has_calls(calls)
        self.assertEqual(self.iproute_obj.link.call_count, 3)

    def test_delete_vnet_interfaces_down_not_delete_veth_interfaces_if_not_in_config(self):
        calls = [call("del", ifname=i) for i in ["vnet-br0", "vnet-br1"]]
        del self.config["veths"]
        delete_vnet_interfaces(self.config)
        self.iproute_obj.link.assert_has_calls(calls)
        self.assertEqual(self.iproute_obj.link.call_count, 2)


class TestStartTcpdumpOnVNetInterface(VNetTestCase):
    def setUp(self) -> None:
        self.popen = self.set_up_patch("vnet_manager.operations.interface.Popen")

    def test_start_tcpdump_on_vnet_interface_makes_correct_popen_call(self):
        start_tcpdump_on_vnet_interface("dev1")
        self.popen.assert_called_once_with(shlex.split(f"tcpdump -i dev1 -U -w {join(settings.VNET_SNIFFER_PCAP_DIR, 'dev1.pcap')}"))
