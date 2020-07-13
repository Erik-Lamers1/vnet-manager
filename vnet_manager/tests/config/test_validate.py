from unittest.mock import Mock, call
from copy import deepcopy

from vnet_manager.tests import VNetTestCase
from vnet_manager.config.validate import ValidateConfig
from vnet_manager.conf import settings


class TestValidateConfigClass(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.provider_config = Mock()
        self.validator.validate_provider_config = self.provider_config
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
        self.provider_config.assert_called_once_with()
        self.switch_config.assert_called_once_with()
        self.machine_config.assert_called_once_with()

    def test_validate_function_does_not_call_veth_validator_when_not_present_in_config(self):
        del self.validator.config["veths"]
        self.validator.validate()
        self.assertFalse(self.veth_config.called)

    def test_validate_function_calls_veth_validator_when_veths_in_config(self):
        self.validator.validate()
        self.veth_config.assert_called_once_with()


class TestValidateConfigValidateProviderConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.base_image_validator = Mock()
        self.validator.validate_base_image_parameters = self.base_image_validator

    def test_validate_provider_config_runs_ok_on_good_config(self):
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.assertGreater(self.validator.validators_ran, 0)

    def test_validate_provider_config_fails_on_missing_providers_config(self):
        del self.validator.config["providers"]
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Providers dict not found in config, this usually means the default config is not correct{}".format(
                self.validator.default_message
            )
        )

    def test_validate_provider_config_fails_when_providers_is_not_a_dict(self):
        self.validator.config["providers"] = 10
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Providers is not a dict, this means the default config is corrupt{}".format(self.validator.default_message)
        )

    def test_validate_provider_config_fails_when_provider_does_not_have_supported_operating_systems(self):
        del self.validator.config["providers"]["lxc"]["supported_operating_systems"]
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "No supported operating systems found for provider lxc{}".format(self.validator.default_message)
        )

    def test_validate_provider_config_fails_when_provider_supported_operating_systems_is_not_a_list(self):
        self.validator.config["providers"]["lxc"]["supported_operating_systems"] = 42
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "supported_operating_systems for provider lxc is not a list{}".format(self.validator.default_message)
        )

    def test_validate_provider_config_sets_dns_nameserver_to_8_8_8_8_when_not_in_provider_config(self):
        del self.validator.config["providers"]["lxc"]["dns-nameserver"]
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["dns-nameserver"], "8.8.8.8")

    def test_validate_provider_config_sets_dns_nameserver_to_8_8_8_8_when_not_a_str(self):
        self.validator.config["providers"]["lxc"]["dns-nameserver"] = 1337
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["dns-nameserver"], "8.8.8.8")

    def test_validate_provider_config_sets_required_host_packages_to_empty_list_when_not_present(self):
        del self.validator.config["providers"]["lxc"]["required_host_packages"]
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["required_host_packages"], [])

    def test_validate_provider_config_sets_required_host_packages_to_empty_list_when_not_a_list(self):
        self.validator.config["providers"]["lxc"]["required_host_packages"] = 42
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["required_host_packages"], [])

    def test_validate_provider_config_sets_guest_packages_to_empty_list_when_not_present(self):
        del self.validator.config["providers"]["lxc"]["guest_packages"]
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["guest_packages"], [])

    def test_validate_provider_config_sets_guest_packages_to_empty_list_when_not_a_list(self):
        self.validator.config["providers"]["lxc"]["guest_packages"] = "os3"
        self.validator.validate_provider_config()
        self.assertTrue(self.validator.config_validation_successful)
        config = self.validator.updated_config
        self.assertEqual(config["providers"]["lxc"]["guest_packages"], [])

    def test_validate_provider_config_fails_when_base_image_not_in_provider_config(self):
        del self.validator.config["providers"]["lxc"]["base_image"]
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with("No base_image found for provider lxc{}".format(self.validator.default_message))

    def test_validate_provider_config_fails_when_base_image_is_not_a_dict(self):
        self.validator.config["providers"]["lxc"]["base_image"] = "os4"
        self.validator.validate_provider_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with("'base_image' for provider lxc is not a dict{}".format(self.validator.default_message))

    def test_validate_provider_config_does_not_calls_base_image_validator_when_with_errors(self):
        del self.validator.config["providers"]["lxc"]["base_image"]
        self.validator.validate_provider_config()
        self.assertFalse(self.base_image_validator.called)

    def test_validate_provider_config_calls_base_image_validator_with_name_of_provider(self):
        self.validator.validate_provider_config()
        self.base_image_validator.assert_called_once_with("lxc")


class TestValidateConfigValidateBaseImageParameters(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")

    def test_validate_base_image_config_runs_ok_on_good_config(self):
        self.validator.validate_base_image_parameters("lxc")
        self.assertTrue(self.validator.config_validation_successful)
        self.assertEqual(self.validator.validators_ran, 0)

    def test_validate_base_image_config_fails_when_os_not_present(self):
        del self.validator.config["providers"]["lxc"]["base_image"]["os"]
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc is missing OS in the base image config{}".format(self.validator.default_message)
        )

    def test_validate_base_image_config_fails_when_os_is_not_a_string(self):
        self.validator.config["providers"]["lxc"]["base_image"]["os"] = 42
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc OS for base image config is not a string{}".format(self.validator.default_message)
        )

    def test_validate_base_image_config_fails_when_server_not_present(self):
        del self.validator.config["providers"]["lxc"]["base_image"]["server"]
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc is missing server in the base image config{}".format(self.validator.default_message)
        )

    def test_validate_base_image_config_fails_when_server_is_not_a_string(self):
        self.validator.config["providers"]["lxc"]["base_image"]["server"] = 42
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc server for base image config is not a string{}".format(self.validator.default_message)
        )

    def test_validate_base_image_config_fails_when_protocol_not_present(self):
        del self.validator.config["providers"]["lxc"]["base_image"]["protocol"]
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc is missing protocol in the base image config{}".format(self.validator.default_message)
        )

    def test_validate_base_image_config_fails_when_protocol_is_not_a_string(self):
        self.validator.config["providers"]["lxc"]["base_image"]["protocol"] = 42
        self.validator.validate_base_image_parameters("lxc")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Provider lxc protocol for base image config is not a string{}".format(self.validator.default_message)
        )


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
        self.logger.error.assert_called_once_with("Config item 'switches' missing{}".format(self.validator.default_message))

    def test_validate_switch_config_fails_when_switch_config_not_a_int(self):
        self.validator.config["switches"] = "os3"
        self.validator.validate_switch_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Config item 'switches: {}' does not seem to be an integer{}".format(
                self.validator.config["switches"], self.validator.default_message
            )
        )


class TestValidateConfigValidateMachineConfig(VNetTestCase):
    def setUp(self) -> None:
        self.validator = ValidateConfig(deepcopy(settings.CONFIG))
        self.logger = self.set_up_patch("vnet_manager.config.validate.logger")
        self.validate_files = Mock()
        self.validate_interfaces = Mock()
        self.validator.validate_interface_config = self.validate_interfaces
        self.validator.validate_machine_files_parameters = self.validate_files

    def test_validate_machine_config_runs_ok_with_good_config(self):
        self.validator.validate_machine_config()
        self.assertTrue(self.validator.config_validation_successful)
        self.assertGreater(self.validator.validators_ran, 0)

    def test_validate_machine_config_fails_when_machine_config_not_present(self):
        del self.validator.config["machines"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with("Config item 'machines' missing{}".format(self.validator.default_message))

    def test_validate_machine_config_fails_when_machine_config_not_a_dict(self):
        self.validator.config["machines"] = 42
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "Machines config is not a dict, this means the user config is incorrect{}".format(self.validator.default_message)
        )

    def test_validate_machine_config_fails_when_machine_type_not_present(self):
        del self.validator.config["machines"]["router100"]["type"]
        self.validator.validate_machine_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with("Type not found for machine router100{}".format(self.validator.default_message))

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
        self.logger.error.assert_called_once_with(
            "Files directive for machine router100 is not a dict{}".format(self.validator.default_message)
        )

    def test_validate_machine_config_succeeds_when_machine_files_not_present(self):
        del self.validator.config["machines"]["router100"]["files"]
        del self.validator.config["machines"]["router101"]["files"]
        del self.validator.config["machines"]["router102"]["files"]
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
            "Machine router100 does not appear to have any interfaces{}".format(self.validator.default_message)
        )

    def test_validate_machine_config_fails_if_interfaces_is_not_a_dict(self):
        self.validator.config["machines"]["router100"]["interfaces"] = 42
        self.validator.config["machines"]["router101"]["interfaces"] = 42
        self.validator.config["machines"]["router102"]["interfaces"] = 42
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

    def test_validate_interface_config_runs_ok_with_good_config(self):
        self.validator.validate_interface_config("router100")
        self.assertTrue(self.validator.config_validation_successful)

    def test_validate_interface_config_fails_when_ipv4_not_present(self):
        del self.validator.config["machines"]["router100"]["interfaces"]["eth12"]["ipv4"]
        self.validator.validate_interface_config("router100")
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "ipv4 not found for interface eth12 on machine router100{}".format(self.validator.default_message)
        )

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
            "bridge keyword missing on interface eth12 for machine router100{}".format(self.validator.default_message)
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
        self.logger.error.assert_called_once_with(
            "Config item: 'veths' does not seem to be a dict {}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_name_if_not_a_string(self):
        self.validator.config["veths"][42] = self.validator.config["veths"].pop("vnet-veth3")
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface name: 42 does not seem to be a string{}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_values_if_not_a_dict(self):
        self.validator.config["veths"]["vnet-veth3"] = "blaap"
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface vnet-veth3 data does not seem to be a dict{}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_bridge_missing(self):
        del self.validator.config["veths"]["vnet-veth3"]["bridge"]
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface vnet-veth3 is missing the bridge parameter{}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_bridge_is_not_a_string(self):
        self.validator.config["veths"]["vnet-veth3"]["bridge"] = 42
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface vnet-veth3 bridge parameter does not seem to be a str{}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_peer_is_not_a_string(self):
        self.validator.config["veths"]["vnet-veth3"]["peer"] = 42
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface vnet-veth3 peer parameter does not seem to be a string{}".format(self.validator.default_message)
        )

    def test_validate_veth_config_fails_when_veth_config_parameter_stp_is_not_a_bool(self):
        self.validator.config["veths"]["vnet-veth3"]["stp"] = "42"
        self.validator.validate_veth_config()
        self.assertFalse(self.validator.config_validation_successful)
        self.logger.error.assert_called_once_with(
            "veth interface vnet-veth3 stp parameter does not seem to be a boolean{}".format(self.validator.default_message)
        )
