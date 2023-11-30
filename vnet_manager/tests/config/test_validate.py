from unittest.mock import Mock, call
from copy import deepcopy

from vnet_manager.tests import VNetTestCase
from vnet_manager.config.validate import ValidateConfig
from vnet_manager.conf import settings


class TestValidateConfigClass(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.switch_config = Mock()
        self.validator.validate_switch_config = self.switch_config
        self.machine_config = Mock()
        self.validator.validate_machine_config = self.machine_config
        self.veth_config = Mock()
        self.validator.validate_veth_config = self.veth_config

    def test_validate_class_returns_all_ok_on_init(self):
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_class_ran_zero_validators_on_init(self):
        self.assertEqual(self.validator.validators_ran, 0)

    def test_validate_class_returns_proper_string_message(self):
        self.assertEqual(str(self.validator), "VNet config validator, current_state: OK, amount of validators run: 0")

    def test_validate_class_returns_original_config_on_init(self):
        self.assertEqual(self.validator.updated_config, settings.CONFIG)

    def test_validate_function_calls_standard_validator_functions(self):
        self.validator.validate()
        self.switch_config.assert_called_once_with()
        self.machine_config.assert_called_once_with()

    def test_validate_function_does_not_call_veth_validator_when_not_present_in_config(self):
        del self.validator.config["veths"]
        self.validator.validate()
        self.assertFalse(self.veth_config.called)

    def test_validate_function_calls_veth_validator_when_veths_in_config(self):
        self.validator.validate()
        self.veth_config.assert_called_once_with()


class TestValidateConfigValidateSwitchConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")

    def test_validate_switch_config_runs_ok_with_good_config(self):
        self.validator.validate_switch_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.assertGreater(self.validator.validators_ran, 0)

    def test_validate_switch_config_fails_when_switch_config_not_present(self):
        del self.validator.config["switches"]
        self.validator.validate_switch_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Config item 'switches' missing{self.validator.default_message}")

    def test_validate_switch_config_fails_when_switch_config_not_a_int(self):
        self.validator.config["switches"] = "os3"
        self.validator.validate_switch_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Config item 'switches: {self.validator.config['switches']}' does not seem to be an integer{self.validator.default_message}"
        )


class TestValidateConfigValidateMachineConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.validate_files = Mock()
        self.validate_interfaces = Mock()
        self.validator.validate_interface_config = self.validate_interfaces
        self.validator.validate_machine_files_parameters = self.validate_files
        self.validate_vlan_config = self.set_up_patch("vnet_manager.config.validate.ValidateConfig.validate_vlan_config")
        self.validate_bridge_config = self.set_up_patch("vnet_manager.config.validate.ValidateConfig.validate_machine_bridge_config")

    def test_validate_machine_config_runs_ok_with_good_config(self):
        self.validator.validate_machine_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.assertGreater(self.validator.validators_ran, 0)

    def test_validate_machine_config_fails_when_machine_config_not_present(self):
        del self.validator.config["machines"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Config item 'machines' missing{self.validator.default_message}")

    def test_validate_machine_config_fails_when_machine_config_not_a_dict(self):
        self.validator.config["machines"] = 42
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Machines config is not a dict, this means the user config is incorrect{self.validator.default_message}"
        )

    def test_validate_machine_config_fails_when_machine_type_not_present(self):
        del self.validator.config["machines"]["router100"]["type"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Type not found for machine router100{self.validator.default_message}")

    def test_validate_machine_config_fails_when_machine_type_not_in_supported_machine_types(self):
        self.validator.config["machines"]["router100"]["type"] = "banana"
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Type banana for machine router100 unsupported. I only support the following types: {}{}".format(
                settings.SUPPORTED_MACHINE_TYPES, self.validator.default_message
            )
        )

    def test_validate_machine_config_fails_when_machine_files_not_a_dict(self):
        self.validator.config["machines"]["router100"]["files"] = "banana"
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Files directive for machine router100 is not a dict{self.validator.default_message}")

    def test_validate_machine_config_succeeds_when_machine_files_not_present(self):
        del self.validator.config["machines"]["router100"]["files"]
        del self.validator.config["machines"]["router101"]["files"]
        del self.validator.config["machines"]["host102"]["files"]
        self.validator.validate_machine_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.assertFalse(self.validate_files.called)

    def test_validate_machine_config_calls_validate_files(self):
        self.validator.validate_machine_config()
        calls = [call(machine) for machine in self.validator.config["machines"].keys()]
        self.validate_files.assert_has_calls(calls)

    def test_validate_machine_config_fails_if_interfaces_not_in_machine_config(self):
        del self.validator.config["machines"]["router100"]["interfaces"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Machine router100 does not appear to have any interfaces{self.validator.default_message}"
        )

    def test_validate_machine_config_fails_if_interfaces_is_not_a_dict(self):
        self.validator.config["machines"]["router100"]["interfaces"] = 42
        self.validator.config["machines"]["router101"]["interfaces"] = 42
        self.validator.config["machines"]["host102"]["interfaces"] = 42
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        calls = [
            call(
                "The interfaces for machine {} are not given as a dict, this usually means a typo in the config{}".format(
                    machine, self.validator.default_message
                )
            )
            for machine in self.validator.config["machines"].keys()
        ]
        self.logger.error.assert_has_calls(calls)
        self.assertFalse(self.validate_interfaces.called)

    def test_validate_machine_config_calls_validate_interface_config(self):
        self.validator.validate_machine_config()
        calls = [call(machine) for machine in self.validator.config["machines"].keys()]
        self.validate_interfaces.assert_has_calls(calls)

    def test_validate_machine_config_calls_validate_vlan_config_for_each_vlan_interface(self):
        # We have only one VLAN interface defined in the settings
        self.validator.validate_machine_config()
        self.validate_vlan_config.assert_called_once_with("router100")

    def test_validate_machine_config_does_not_call_validate_vlan_config_if_not_vlans_present(self):
        del self.validator.config["machines"]["router100"]["vlans"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validate_vlan_config.called)

    def test_validate_machine_config_fails_if_vlans_is_not_a_dict(self):
        self.validator.config["machines"]["router100"]["vlans"] = 1337
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Machine router100 has a VLAN config but it does not appear to be a dict, "
            "this usually means a typo in the config{}".format(self.validator.default_message)
        )

    def test_validate_machine_config_does_not_call_validate_bridge_config_if_no_bridges(self):
        del self.validator.config["machines"]["router100"]["bridges"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validate_bridge_config.called)

    def test_validate_machine_config_calls_validate_bridge_config_for_machines_with_bridges(self):
        self.validator.validate_machine_config()
        self.validate_bridge_config.assert_called_once_with("router100")

    def test_validate_machine_config_fails_if_bridge_config_is_not_a_dict(self):
        self.validator.config["machines"]["router100"]["bridges"] = 1337
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once()

    def test_validate_interface_config_sexagesimal_mac_address(self):
        # 0d33212743741 is the sexagesimal representation of 42:42:42:42:09:01
        # cf. https://github.com/Erik-Lamers1/vnet-manager/issues/62
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["mac"] = 33212743741
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"MAC 33212743741 for interface eth12 on machine router100 was parsed as a sexagesimal integer. Please wrap the MAC address between 'quotes'"
        )

    def test_validate_interface_config_invalid_mac_address(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["mac"] = "gg:hh:ii:jj:kk:ll"
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"MAC gg:hh:ii:jj:kk:ll for interface eth12 on machine router100, does not seem to be valid. Please check your settings"
        )


class TestValidateConfigValidateMachineFilesParameters(VNetTestCase):
    def setUp(self) -> None:
        # Use VALIDATED_CONFIG so we have the config_dir
        self.validator = ValidateConfig(deepcopy(settings.VALIDATED_CONFIG))
        self.is_dir = self.set_up_patch("vnet_manager.config.validate.isdir")
        self.is_dir.return_value = False
        self.is_file = self.set_up_patch("vnet_manager.config.validate.isfile")
        self.is_file.return_value = False
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")

    def test_validate_machine_file_parameters_fails_when_no_file_or_dir_found(self):
        self.validator.validate_machine_files_parameters("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.assertTrue(self.logger.error.called)

    def test_validate_machine_file_parameters_is_ok_when_is_dir_is_true(self):
        self.is_dir.return_value = True
        self.validator.validate_machine_files_parameters("router100")
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_machine_file_parameters_is_ok_when_is_file_is_true(self):
        self.is_file.return_value = True
        self.validator.validate_machine_files_parameters("router100")
        self.assertTrue(self.validator.config_validation_successful)


class TestValidateConfigValidateInterfaceConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.validate_routes = self.set_up_patch("vnet_manager.config.validate.ValidateConfig.validate_interface_routes")

    def test_validate_interface_config_runs_ok_with_good_config(self):
        self.validator.validate_interface_config("router100")
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_interface_config_runs_ok_if_ipv4_not_present(self):
        del self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["ipv4"]
        self.validator.validate_interface_config("router100")
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_interface_config_fails_when_ipv4_not_valid(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["ipv4"] = "255.255.256.257"
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once()

    def test_validate_interface_config_does_not_fail_when_ipv6_not_present(self):
        del self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["ipv6"]
        self.validator.validate_interface_config("router100")
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_interface_config_fails_when_ipv6_not_valid(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["ipv6"] = "2001:h80:1:2d96::f1a5/64"
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once()

    def test_validate_interface_config_fails_when_bridge_not_present(self):
        del self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["bridge"]
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"bridge keyword missing on interface eth12 for machine router100{self.validator.default_message}"
        )

    def test_validate_interface_config_fails_when_bridge_not_a_int(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["bridge"] = "42"
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Invalid bridge number detected for interface eth12 on machine router100. "
            "The bridge keyword should correspond to the interface number of the vnet bridge to connect to "
            "(starting at iface number 0)"
        )

    def test_validate_interface_config_fails_when_bridge_number_higher_then_the_amount_of_switches(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["bridge"] = 3
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Invalid bridge number detected for interface eth12 on machine router100. "
            "The bridge keyword should correspond to the interface number of the vnet bridge to connect to "
            "(starting at iface number 0)"
        )

    def test_validate_interface_config_fails_when_routes_is_not_a_list(self):
        self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["routes"] = "blaap"
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"routes passed to interface eth12 for machine router100, found type str, expected type 'list'{self.validator.default_message}"
        )

    def test_validate_interface_config_calls_validate_routes_when_routes_passed_in_config(self):
        self.validator.validate_interface_config("router100")
        self.validate_routes.assert_called_once_with(
            self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["routes"], "eth12", "router100"
        )

    def test_validate_interface_config_does_not_call_validate_routes_when_no_routes_passed(self):
        del self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["routes"]
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validate_routes.called)


class TestValidateInterfaceRoutes(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.machine = "router100"
        self.routes = deepcopy(settings.CONFIG["machines"]["router100"]["interfaces"]["eth12"]["routes"])

    def test_validate_routes_validates_correct_routes(self):
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertTrue(self.validator.config_validation_successful)
        self.assertFalse(self.logger.error.called)

    def test_validate_routes_fails_if_route_missing_to(self):
        del self.routes[0]["to"]
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"'to' keyword missing from route 1 on interface eth12 for machine {self.machine}{self.validator.default_message}"
        )

    def test_validate_routes_fails_if_to_is_malformed(self):
        self.routes[0]["to"] = "1negen2.168.0.1"
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Invalid 'to' value 1negen2.168.0.1 for route 1 on interface eth12 for machine {self.machine}{self.validator.default_message}"
        )

    def test_validate_routes_fails_if_route_missing_via(self):
        del self.routes[0]["via"]
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"'via' keyword missing from route 1 on interface eth12 for machine {self.machine}{self.validator.default_message}"
        )

    def test_validate_routes_fails_if_via_is_malformed(self):
        self.routes[1]["via"] = "blaap"
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Invalid 'via' value blaap (not an IP address) for route 2 on interface eth12 for machine {}{}".format(
                self.machine, self.validator.default_message
            )
        )

    def test_validate_routes_updates_default_route_to_quad_zero(self):
        self.validator.validate_interface_routes(self.routes, "eth12", self.machine)
        self.assertEqual(self.validator.updated_config["machines"][self.machine]["interfaces"]["eth12"]["routes"][1]["to"], "0.0.0.0/0")


class TestValidateConfigValidateVethConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")

    def test_validate_veth_config_does_nothing_when_veth_config_not_present(self):
        del self.validator.config["veths"]
        self.validator.validate_veth_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.logger.warning.assert_called_once_with("Tried to validate veth config, but no veth config present, skipping...")

    def test_validate_veth_config_fails_when_veth_config_is_not_a_dict(self):
        self.validator.config["veths"] = 42
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Config item: 'veths' does not seem to be a dict {self.validator.default_message}")

    def test_validate_veth_config_fails_when_veth_config_name_if_not_a_string(self):
        self.validator.config["veths"][42] = self.validator.config["veths"].pop("vnet-veth1")
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"veth interface name: 42 does not seem to be a string{self.validator.default_message}")

    def test_validate_veth_config_fails_when_veth_config_values_if_not_a_dict(self):
        self.validator.config["veths"]["vnet-veth1"] = "blaap"
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"veth interface vnet-veth1 data does not seem to be a dict{self.validator.default_message}"
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_bridge_missing(self):
        del self.validator.config["veths"]["vnet-veth1"]["bridge"]
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"veth interface vnet-veth1 is missing the bridge parameter{self.validator.default_message}"
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_bridge_is_not_a_string(self):
        self.validator.config["veths"]["vnet-veth1"]["bridge"] = 42
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"veth interface vnet-veth1 bridge parameter does not seem to be a str{self.validator.default_message}"
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_peer_is_not_a_string(self):
        self.validator.config["veths"]["vnet-veth1"]["peer"] = 42
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"veth interface vnet-veth1 peer parameter does not seem to be a string{self.validator.default_message}"
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_stp_is_not_a_bool(self):
        self.validator.config["veths"]["vnet-veth1"]["stp"] = "42"
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"veth interface vnet-veth1 stp parameter does not seem to be a boolean{self.validator.default_message}"
        )


class TestValidateConfigValidateVLANConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.machine = "router100"

    def test_validate_vlan_config_is_successful_is_everything_okay(self):
        self.validator.validate_vlan_config(self.machine)
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_vlan_config_fails_is_id_is_not_present(self):
        del self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["id"]
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"VLAN vlan.100 on machine {self.machine} is missing it's vlan id{self.validator.default_message}"
        )

    def test_validate_vlan_config_fails_if_id_is_not_castable_to_int(self):
        self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["id"] = "banaan"
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Unable to cast VLAN vlan.100 with ID banaan from machine {self.machine} to a integer{self.validator.default_message}"
        )

    def test_validate_vlan_config_fails_if_link_is_not_present(self):
        del self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["link"]
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"VLAN vlan.100 on machine {self.machine} is missing it's link attribute{self.validator.default_message}"
        )

    def test_validate_vlan_config_fails_if_link_is_not_a_string(self):
        self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["link"] = 42
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            f"Link 42 for VLAN vlan.100 on machine {self.machine}, does not seem to be a string{self.validator.default_message}"
        )

    def test_validate_vlan_config_fails_if_link_is_not_found_in_machine_interfaces(self):
        self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["link"] = "eth1337"
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Link eth1337 for VLAN vlan.100 on machine {} does not correspond to any interfaces on "
            "the same machine{}".format(self.machine, self.validator.default_message)
        )

    def test_validate_vlan_config_does_not_check_link_in_interfaces_if_config_validation_already_failed(self):
        self.validator._all_ok = False
        self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["link"] = "eth1337"
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.logger.error.called)

    def test_validate_vlan_config_does_not_fail_if_addresses_not_in_values(self):
        del self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["addresses"]
        self.validator.validate_vlan_config(self.machine)
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_vlan_config_fails_if_invalid_address_in_addresses(self):
        self.validator.config["machines"][self.machine]["vlans"]["vlan.100"]["addresses"].append("banaan")
        self.validator.validate_vlan_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.assertTrue(self.logger.error.call_args_list[0].startswith(f"Address banaan for VLAN vlan.100 on machine {self.machine}"))


class TestValidateConfigValidateMachineBridgeConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.machine = "router100"

    def test_validate_machine_bridge_config_is_successful_with_correct_bridge_config(self):
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_machine_bridge_config_accepts_missing_ipv4(self):
        del self.validator.config["machines"][self.machine]["bridges"]["br1"]["ipv4"]
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_machine_bridge_config_accepts_missing_ipv6(self):
        del self.validator.config["machines"][self.machine]["bridges"]["br1"]["ipv6"]
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_machine_bridge_config_fails_if_incorrect_ipv4(self):
        self.validator.config["machines"][self.machine]["bridges"]["br1"]["ipv4"] = "blaap"
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once()

    def test_validate_machine_bridge_config_fails_if_incorrect_ipv6(self):
        self.validator.config["machines"][self.machine]["bridges"]["br1"]["ipv6"] = "blaap"
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once()

    def test_validate_machine_bridge_config_fails_if_slaves_not_in_bridge_params(self):
        del self.validator.config["machines"][self.machine]["bridges"]["br1"]["slaves"]
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Bridge br1 on machine {self.machine} does not have any slaves")

    def test_validate_machine_bridge_config_fails_if_slaves_param_is_not_a_list(self):
        self.validator.config["machines"][self.machine]["bridges"]["br1"]["slaves"] = "blaap"
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Slaves on bridge br1 for machine {self.machine}, is not formatted as a list")

    def test_validate_machine_bridge_config_fails_if_slave_not_present_in_interfaces_config(self):
        iface = "blaap1"
        self.validator.config["machines"][self.machine]["bridges"]["br1"]["slaves"].append(iface)
        self.validator.validate_machine_bridge_config(self.machine)
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(f"Undefined slave interface {iface} assigned to bridge br1 on machine {self.machine}")
