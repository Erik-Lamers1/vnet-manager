from os import EX_OK, EX_USAGE
from unittest.mock import MagicMock

from vnet_manager.tests import VNetTestCase
from vnet_manager.actions.manager import action_manager
from vnet_manager.conf import settings


class TestActionManager(VNetTestCase):
    def setUp(self) -> None:
        self.get_config = self.set_up_patch("vnet_manager.actions.manager.get_config")
        self.validator = MagicMock()
        self.validate = self.set_up_patch("vnet_manager.actions.manager.ValidateConfig")
        self.validate.return_value = self.validator
        self.validator.updated_config = {}
        self.show_version = self.set_up_patch("vnet_manager.actions.manager.show_version")
        self.show_status = self.set_up_patch("vnet_manager.actions.manager.show_status")
        self.show_status_interfaces = self.set_up_patch("vnet_manager.actions.manager.show_vnet_interface_status")
        self.show_status_interfaces_veth = self.set_up_patch("vnet_manager.actions.manager.show_vnet_veth_interface_status")
        self.bring_up_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.bring_up_vnet_interfaces")
        self.change_machine_status = self.set_up_patch("vnet_manager.actions.manager.change_machine_status")
        self.bring_down_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.bring_down_vnet_interfaces")
        self.ensure_vnet_lxc_environment = self.set_up_patch("vnet_manager.actions.manager.ensure_vnet_lxc_environment")
        self.create_machines = self.set_up_patch("vnet_manager.actions.manager.create_machines")
        self.put_files_on_machine = self.set_up_patch("vnet_manager.actions.manager.put_files_on_machine")
        self.generate_vnet_hosts_file = self.set_up_patch("vnet_manager.actions.manager.generate_vnet_hosts_file")
        self.place_vnet_hosts_file_on_machines = self.set_up_patch("vnet_manager.actions.manager.place_vnet_hosts_file_on_machines")
        self.enable_type_specific_machine_configuration = self.set_up_patch(
            "vnet_manager.actions.manager.enable_type_specific_machine_configuration"
        )
        self.request_confirmation = self.set_up_patch("vnet_manager.actions.manager.request_confirmation")
        self.destroy_lxc_image = self.set_up_patch("vnet_manager.actions.manager.destroy_lxc_image")
        self.destroy_machines = self.set_up_patch("vnet_manager.actions.manager.destroy_machines")
        self.delete_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.delete_vnet_interfaces")

    def test_action_raises_not_implemented_error_if_unsupported_action(self):
        with self.assertRaises(NotImplementedError):
            action_manager("not_working", "blaap")

    def test_action_manager_calls_show_version_with_version_action(self):
        ret = action_manager("version", "blaap")
        self.show_version.assert_called_once_with()
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_get_config(self):
        action_manager("list", "blaap")
        self.get_config.assert_called_once_with("blaap")

    def test_action_manager_calls_validate_config(self):
        action_manager("list", "blaap")
        self.validate.called_once_with()

    def test_action_manager_called_validator_function(self):
        action_manager("list", "blaap")
        self.validator.validate.assert_called_once()

    def test_action_manager_returns_usage_exit_code_if_validator_unsuccessful(self):
        self.validator.config_validation_successful = False
        ret = action_manager("list", "blaap")
        self.assertEqual(ret, EX_USAGE)
        self.assertFalse(self.show_status.called)

    def test_action_manager_calls_show_status_with_list_action(self):
        action_manager("list", "blaap")
        self.show_status.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_show_vnet_interface_status_with_list_action(self):
        action_manager("list", "blaap")
        self.show_status_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_vnet_veth_interface_status_with_list_action_if_veths_config_not_present(self):
        action_manager("list", "blaap")
        self.assertFalse(self.show_status_interfaces_veth.called)

    def test_action_manager_calls_show_vnet_veth_interface_status_with_list_action(self):
        self.validator.updated_config["veths"] = "jajaja"
        action_manager("list", "blaap")
        self.show_status_interfaces_veth.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_returns_ex_ok_after_action_has_been_completed(self):
        ret = action_manager("list", "blaap")
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_bring_up_vnet_interfaces_with_start_action(self):
        action_manager("start", "blaap")
        self.bring_up_vnet_interfaces.assert_called_once_with(self.validator.updated_config, sniffer=False)
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_calls_bring_up_vnet_interfaces_with_start_action_and_sniffer(self):
        action_manager("start", "blaap", sniffer=True)
        self.bring_up_vnet_interfaces.assert_called_once_with(self.validator.updated_config, sniffer=True)

    def test_action_manager_calls_change_machine_status_with_start_action(self):
        action_manager("start", "blaap")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="start")

    def test_action_manager_calls_change_machine_status_with_start_action_and_machines(self):
        action_manager("start", "blaap", machines=["machine"])
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="start")

    def test_action_manager_calls_change_machine_status_with_stop_action(self):
        action_manager("stop", "blaap")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="stop")

    def test_action_manager_calls_change_machine_status_with_stop_action_and_machines(self):
        action_manager("stop", "blaap", machines=["machine"])
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="stop")

    def test_action_manager_calls_bring_down_vnet_interfaces_with_stop_action(self):
        action_manager("stop", "blaap")
        self.bring_down_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_bring_down_vnet_interfaces_with_stop_action_and_machines(self):
        action_manager("stop", "blaap", machines=["machine"])
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_calls_ensure_vnet_lxc_environment_with_create_action(self):
        action_manager("create", "blaap")
        self.ensure_vnet_lxc_environment.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_create_machines_with_create_action(self):
        action_manager("create", "blaap")
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_create_machines_with_create_action_and_machines(self):
        action_manager("create", "blaap", machines=["machine"])
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])

    def test_action_manager_calls_put_files_on_machine_with_create_action(self):
        action_manager("create", "blaap")
        self.put_files_on_machine.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_generate_vnet_hosts_file_with_create_action(self):
        action_manager("create", "blaap")
        self.generate_vnet_hosts_file.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_enable_type_specific_machine_configuration(self):
        action_manager("create", "blaap")
        self.enable_type_specific_machine_configuration.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_destroy_machines_with_destroy_action(self):
        action_manager("destroy", "blaaap")
        self.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_destroy_machines_with_destroy_action_and_machines(self):
        action_manager("destroy", "blaaap", machines=["machine"])
        self.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])
        self.assertFalse(self.destroy_lxc_image.called)

    def test_action_manager_calls_delete_vnet_interfaces_with_destroy_action(self):
        action_manager("destroy", "blaap")
        self.delete_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_delete_vnet_interfaces_with_destroy_action_and_machines(self):
        action_manager("destroy", "blaap", machines=["machine"])
        self.assertFalse(self.delete_vnet_interfaces.called)

    def test_action_manager_calls_destroy_lxc_image_with_destroy_action_and_base_image(self):
        action_manager("destroy", "blaap", base_image=True)
        self.destroy_lxc_image.assert_called_once_with(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True)
        self.assertFalse(self.destroy_machines.called)

    def test_action_manager_calls_request_confirmation_with_destroy_action_and_base_image(self):
        action_manager("destroy", "blaap", base_image=True)
        self.request_confirmation.assert_called_once_with(prompt="Are you sure you want to delete the VNet base images (y/n)? ")
