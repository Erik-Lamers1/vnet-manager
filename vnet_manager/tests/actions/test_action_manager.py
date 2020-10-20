from os import EX_OK, EX_USAGE
from unittest.mock import MagicMock

from vnet_manager.tests import VNetTestCase
from vnet_manager.actions.manager import ActionManager
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
        self.cleanup_vnet_lxc_environment = self.set_up_patch("vnet_manager.actions.manager.cleanup_vnet_lxc_environment")
        self.display_help_for_action = self.set_up_patch("vnet_manager.actions.manager.display_help_for_action")
        self.isfile = self.set_up_patch("vnet_manager.actions.manager.isfile")
        self.isdir = self.set_up_patch("vnet_manager.actions.manager.isdir")
        self.get_yaml_file_from_disk_path = self.set_up_patch("vnet_manager.actions.manager.get_yaml_file_from_disk_path")
        self.get_yaml_file_from_disk_path.return_value = ["file1"]

    def test_action_raises_not_implemented_error_if_unsupported_action(self):
        manager = ActionManager()
        with self.assertRaises(NotImplementedError):
            manager.execute("not_working")

    def test_action_manager_calls_show_version_with_version_action(self):
        manager = ActionManager()
        ret = manager.execute("version")
        self.show_version.assert_called_once_with()
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_display_help_for_action_when_action_has_been_called_with_help_as_second_parameter(self):
        manager = ActionManager(config_path="help")
        ret = manager.execute("start")
        self.display_help_for_action.assert_called_once_with("start")
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_get_config(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.get_config.assert_called_once_with("blaap")

    def test_action_manager_calls_validate_config(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.validate.called_once_with()

    def test_action_manager_called_validator_function(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.validator.validate.assert_called_once()

    def test_action_manager_returns_usage_exit_code_if_validator_unsuccessful(self):
        self.validator.config_validation_successful = False
        manager = ActionManager(config_path="blaap")
        ret = manager.execute("show")
        self.assertEqual(ret, EX_USAGE)
        self.assertFalse(self.show_status.called)

    def test_action_manager_calls_show_status_with_list_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.show_status.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_show_vnet_interface_status_with_list_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.show_status_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_vnet_veth_interface_status_with_list_action_if_veths_config_not_present(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertFalse(self.show_status_interfaces_veth.called)

    def test_action_manager_calls_show_vnet_veth_interface_status_with_list_action(self):
        self.validator.updated_config["veths"] = "jajaja"
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.show_status_interfaces_veth.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_get_yaml_file_from_disk_path_with_list_action(self):
        self.isfile.return_value = False
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.get_yaml_file_from_disk_path.assert_called_once_with("blaap")

    def test_action_manager_calls_show_status_with_return_values_of_get_yaml_files(self):
        self.get_yaml_file_from_disk_path.return_value = ["file1", "file2", "file3"]
        self.isfile.return_value = False
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertEqual(3, self.show_status.call_count)

    def test_action_manager_does_nothing_when_not_file_and_not_dir_with_list_action(self):
        self.isfile.return_value = False
        self.isdir.return_value = False
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertFalse(self.get_yaml_file_from_disk_path.called)
        self.assertFalse(self.show_status.called)

    def test_action_manager_calls_show_status_with_show_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("show")
        self.show_status.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_show_vnet_interface_status_with_show_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("show")
        self.show_status_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_vnet_veth_interface_status_with_show_action_if_veths_config_not_present(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("show")
        self.assertFalse(self.show_status_interfaces_veth.called)

    def test_action_manager_calls_show_vnet_veth_interface_status_with_show_action(self):
        self.validator.updated_config["veths"] = "jajaja"
        manager = ActionManager(config_path="blaap")
        manager.execute("show")
        self.show_status_interfaces_veth.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_returns_ex_ok_after_action_has_been_completed(self):
        manager = ActionManager(config_path="blaap")
        ret = manager.execute("list")
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_bring_up_vnet_interfaces_with_start_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("start")
        self.bring_up_vnet_interfaces.assert_called_once_with(self.validator.updated_config, sniffer=False)
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_calls_bring_up_vnet_interfaces_with_start_action_and_sniffer(self):
        manager = ActionManager(config_path="blaap", sniffer=True)
        manager.execute("start")
        self.bring_up_vnet_interfaces.assert_called_once_with(self.validator.updated_config, sniffer=True)

    def test_action_manager_calls_change_machine_status_with_start_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("start")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="start")

    def test_action_manager_calls_change_machine_status_with_start_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("start")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="start")

    def test_action_manager_calls_change_machine_status_with_stop_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="stop")

    def test_action_manager_calls_change_machine_status_with_stop_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("stop")
        self.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="stop")

    def test_action_manager_calls_bring_down_vnet_interfaces_with_stop_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.bring_down_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_bring_down_vnet_interfaces_with_stop_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("stop")
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_calls_ensure_vnet_lxc_environment_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.ensure_vnet_lxc_environment.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_create_machines_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_create_machines_with_create_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("create")
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])

    def test_action_manager_calls_put_files_on_machine_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.put_files_on_machine.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_generate_vnet_hosts_file_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.generate_vnet_hosts_file.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_enable_type_specific_machine_configuration(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.enable_type_specific_machine_configuration.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_ensure_vnet_lxc_environment_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.ensure_vnet_lxc_environment.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_create_machines_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_create_machines_with_create_action_and_machines_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.machines = ["machine"]
        manager.execute("create")
        self.create_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])

    def test_action_manager_calls_put_files_on_machine_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.put_files_on_machine.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_generate_vnet_hosts_file_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.generate_vnet_hosts_file.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_enable_type_specific_machine_configuration_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.enable_type_specific_machine_configuration.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_destroy_machines_with_destroy_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("destroy")
        self.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_cleanup_vnet_lxc_environment_with_clean_action(self):
        manager = ActionManager()
        manager.execute("clean")
        self.cleanup_vnet_lxc_environment.assert_called_once_with()

    def test_action_manager_calls_destroy_machines_with_destroy_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("destroy")
        self.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])
        self.assertFalse(self.destroy_lxc_image.called)

    def test_action_manager_calls_delete_vnet_interfaces_with_destroy_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("destroy")
        self.delete_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_delete_vnet_interfaces_with_destroy_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("destroy")
        self.assertFalse(self.delete_vnet_interfaces.called)

    def test_action_manager_calls_destroy_lxc_image_with_destroy_action_and_base_image(self):
        manager = ActionManager(config_path="blaap", base_image=True)
        manager.execute("destroy")
        self.destroy_lxc_image.assert_called_once_with(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True)
        self.assertFalse(self.destroy_machines.called)

    def test_action_manager_calls_request_confirmation_with_destroy_action_and_base_image(self):
        manager = ActionManager(config_path="blaap", base_image=True)
        manager.execute("destroy")
        self.request_confirmation.assert_called_once_with(prompt="Are you sure you want to delete the VNet base images (y/n)? ")

    def test_action_manager_has_machine_property(self):
        manager = ActionManager()
        manager.machines = ["1", "2", "3"]
        self.assertEqual(manager.machines, ["1", "2", "3"])
        self.assertIsInstance(ActionManager.machines, property)
