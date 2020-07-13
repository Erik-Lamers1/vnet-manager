from unittest.mock import Mock
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
        self.validator.validate()
        self.assertFalse(self.veth_config.called)

    def test_validate_function_calls_veth_validator_when_veths_in_config(self):
        self.validator.config["veths"] = "ajjaja"
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
