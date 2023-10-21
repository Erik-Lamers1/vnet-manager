from os import EX_OK, EX_USAGE, EX_OSERR
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
        self.machine_op = self.set_up_patch("vnet_manager.actions.manager.machine_op")
        self.show_version = self.set_up_patch("vnet_manager.actions.manager.show_version")
        self.show_status_interfaces = self.set_up_patch("vnet_manager.actions.manager.show_vnet_interface_status")
        self.show_status_interfaces_veth = self.set_up_patch("vnet_manager.actions.manager.show_vnet_veth_interface_status")
        self.bring_up_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.bring_up_vnet_interfaces")
        self.bring_down_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.bring_down_vnet_interfaces")
        self.bring_down_vnet_interfaces.return_value = False
        self.ensure_vnet_lxc_environment = self.set_up_patch("vnet_manager.actions.manager.ensure_vnet_lxc_environment")
        self.put_files_on_machine = self.set_up_patch("vnet_manager.actions.manager.put_files_on_machine")
        self.generate_vnet_hosts_file = self.set_up_patch("vnet_manager.actions.manager.generate_vnet_hosts_file")
        self.place_vnet_hosts_file_on_machines = self.set_up_patch("vnet_manager.actions.manager.place_vnet_hosts_file_on_machines")
        self.request_confirmation = self.set_up_patch("vnet_manager.actions.manager.request_confirmation")
        self.destroy_lxc_image = self.set_up_patch("vnet_manager.actions.manager.destroy_lxc_image")
        self.delete_vnet_interfaces = self.set_up_patch("vnet_manager.actions.manager.delete_vnet_interfaces")
        self.kill_tcpdump_processes_on_vnet_interfaces = self.set_up_patch(
            "vnet_manager.actions.manager.kill_tcpdump_processes_on_vnet_interfaces"
        )
        self.cleanup_vnet_lxc_environment = self.set_up_patch("vnet_manager.actions.manager.cleanup_vnet_lxc_environment")
        self.isdir = self.set_up_patch("vnet_manager.actions.manager.isdir")
        self.write_file = self.set_up_patch("vnet_manager.actions.manager.write_file_to_disk")
        self.get_yaml_file_from_disk_path = self.set_up_patch("vnet_manager.actions.manager.get_yaml_files_from_disk_path")
        self.get_yaml_file_from_disk_path.return_value = ["file1"]

    def test_action_manager_returns_usage_exit_code_if_action_does_not_exist(self):
        ret = ActionManager().execute("blaap")
        self.assertEqual(ret, EX_USAGE)

    def test_action_manager_calls_show_version_with_version_action(self):
        manager = ActionManager()
        ret = manager.execute("version")
        self.show_version.assert_called_once_with()
        self.assertEqual(ret, EX_OK)

    def test_action_manager_calls_get_config(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.get_config.assert_called_once_with("file1")

    def test_action_manager_calls_validate_config(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.validate.called_once_with()

    def test_action_manager_called_validator_function(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.validator.validate.assert_called_once()

    def test_action_manager_does_not_show_status_of_non_valid_config_files(self):
        self.validator.config_validation_successful = False
        self.get_yaml_file_from_disk_path.return_value = ["file1", "file2"]
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertFalse(self.machine_op.show_status.called)

    def test_action_manager_returns_usage_exit_code_if_validator_unsuccessful(self):
        self.validator.config_validation_successful = False
        manager = ActionManager(config_path="blaap")
        ret = manager.execute("show")
        self.assertEqual(ret, EX_USAGE)
        self.assertFalse(self.machine_op.show_status.called)

    def test_action_manager_calls_show_status_with_list_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.machine_op.show_status.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_get_yaml_file_from_disk_path_with_list_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.get_yaml_file_from_disk_path.assert_called_once_with("blaap")

    def test_action_manager_calls_show_status_with_return_values_of_get_yaml_files(self):
        self.get_yaml_file_from_disk_path.return_value = ["file1", "file2", "file3"]
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertEqual(3, self.machine_op.show_status.call_count)

    def test_action_manager_does_nothing_when_not_file_and_not_dir_with_list_action(self):
        self.isdir.return_value = False
        manager = ActionManager(config_path="blaap")
        manager.execute("list")
        self.assertFalse(self.get_yaml_file_from_disk_path.called)
        self.assertFalse(self.machine_op.show_status.called)

    def test_action_manager_returns_os_error_exit_code_when_not_dir_with_list_action(self):
        self.isdir.return_value = False
        manager = ActionManager(config_path="blaap")
        ret = manager.execute("list")
        self.assertEqual(ret, EX_OSERR)

    def test_action_manager_calls_show_status_with_show_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("show")
        self.machine_op.show_status.assert_called_once_with(self.validator.updated_config)

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
        self.bring_up_vnet_interfaces.assert_called_once_with(
            self.validator.updated_config, sniffer=False, pcap_dir=settings.VNET_SNIFFER_PCAP_DIR
        )
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_calls_bring_up_vnet_interfaces_with_start_action_and_sniffer(self):
        manager = ActionManager(config_path="blaap", sniffer=True)
        manager.execute("start")
        self.bring_up_vnet_interfaces.assert_called_once_with(
            self.validator.updated_config, sniffer=True, pcap_dir=settings.VNET_SNIFFER_PCAP_DIR
        )

    def test_action_manager_calls_change_machine_status_with_start_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("start")
        self.machine_op.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="start")

    def test_action_manager_calls_change_machine_status_with_start_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("start")
        self.machine_op.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="start")

    def test_action_manager_calls_change_machine_status_with_stop_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.machine_op.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=None, status="stop")

    def test_action_manager_calls_change_machine_status_with_stop_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("stop")
        self.machine_op.change_machine_status.assert_called_once_with(self.validator.updated_config, machines=["machine"], status="stop")

    def test_action_manager_calls_bring_down_vnet_interfaces_with_stop_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.bring_down_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_does_not_call_bring_down_vnet_interfaces_with_stop_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("stop")
        self.assertFalse(self.bring_down_vnet_interfaces.called)

    def test_action_manager_does_not_call_kill_tcpdump_processes_when_no_lingering_sniffers_are_found(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.assertFalse(self.kill_tcpdump_processes_on_vnet_interfaces.called)

    def test_action_manager_calls_kill_tcpdump_processes_when_lingering_sniffers_are_found(self):
        self.bring_down_vnet_interfaces.return_value = True
        manager = ActionManager(config_path="blaap")
        manager.execute("stop")
        self.kill_tcpdump_processes_on_vnet_interfaces.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_ensure_vnet_lxc_environment_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.ensure_vnet_lxc_environment.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_create_machines_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.machine_op.create_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_create_machines_with_create_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("create")
        self.machine_op.create_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])

    def test_action_manager_calls_put_files_on_machine_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.put_files_on_machine.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_place_vnet_hosts_file_on_machines_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.place_vnet_hosts_file_on_machines.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_generate_vnet_hosts_file_with_create_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.generate_vnet_hosts_file.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_enable_type_specific_machine_configuration(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("create")
        self.machine_op.enable_type_specific_machine_configuration.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_ensure_vnet_lxc_environment_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.ensure_vnet_lxc_environment.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_create_machines_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.machine_op.create_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_create_machines_with_create_action_and_machines_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.machines = ["machine"]
        manager.execute("create")
        self.machine_op.create_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])

    def test_action_manager_calls_put_files_on_machine_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.put_files_on_machine.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_place_vnet_hosts_file_on_machines_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.assertFalse(self.place_vnet_hosts_file_on_machines.called)

    def test_action_manager_calls_generate_vnet_hosts_file_with_create_action_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.assertFalse(self.generate_vnet_hosts_file.called)

    def test_action_manager_calls_enable_type_specific_machine_configuration_and_nohosts(self):
        manager = ActionManager(config_path="blaap", no_hosts=True)
        manager.execute("create")
        self.machine_op.enable_type_specific_machine_configuration.assert_called_once_with(self.validator.updated_config)

    def test_action_manager_calls_destroy_machines_with_destroy_action(self):
        manager = ActionManager(config_path="blaap")
        manager.execute("destroy")
        self.machine_op.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=None)

    def test_action_manager_calls_destroy_machines_with_destroy_action_and_machines(self):
        manager = ActionManager(config_path="blaap")
        manager.machines = ["machine"]
        manager.execute("destroy")
        self.machine_op.destroy_machines.assert_called_once_with(self.validator.updated_config, machines=["machine"])
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
        self.assertFalse(self.machine_op.destroy_machines.called)

    def test_action_manager_calls_request_confirmation_with_destroy_action_and_base_image(self):
        manager = ActionManager(config_path="blaap", base_image=True)
        manager.execute("destroy")
        self.request_confirmation.assert_called_once_with(prompt="Are you sure you want to delete the VNet base images (y/n)? ")

    def test_action_manager_has_machine_property(self):
        manager = ActionManager()
        manager.machines = ["1", "2", "3"]
        self.assertEqual(manager.machines, ["1", "2", "3"])

    def test_action_manager_calls_connect_to_lxc_machine(self):
        manager = ActionManager(config_path="machine1")
        manager.execute("connect")
        self.machine_op.connect_to_lxc_machine.assert_called_once_with("machine1")

    def test_action_manager_returns_usage_exit_code_with_non_supported_provider(self):
        manager = ActionManager(config_path="machine1", provider="blaap133")
        ret = manager.execute("connect")
        self.assertEqual(ret, EX_USAGE)

    def test_action_manager_calls_cleanup_lxc_environment_with_purge_action_on_destroy(self):
        manager = ActionManager(purge=True)
        manager.execute("destroy")
        self.cleanup_vnet_lxc_environment.assert_called_once_with()

    def test_action_manager_writes_bash_completion_file(self):
        manager = ActionManager()
        manager.execute("bash_completion")
        actions = ("create", "connect", "destroy", "list", "show", "status", "start", "stop")
        self.write_file.assert_called_once_with(
            settings.VNET_BASH_COMPLETION_PATH,
            settings.VNET_BASH_COMPLETION_TEMPLATE.format(
                options=" ".join(actions), name=settings.get("PYTHON_PACKAGE_NAME", "vnet-manager")
            ),
        )
